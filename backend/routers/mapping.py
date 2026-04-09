from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from database import supabase
from dependencies import get_current_user
from services.ai.account_mapper import map_accounts
from services.parser.excel_parser import TBRow
from decimal import Decimal

router = APIRouter()


async def _check_project_access(project_id: str, user_id: str, roles=("admin", "auditor")) -> dict:
    project = (
        supabase.table("projects")
        .select("*")
        .eq("id", project_id)
        .is_("deleted_at", "null")
        .single()
        .execute()
    )
    if not project.data:
        raise HTTPException(404, "Project not found")
    member = (
        supabase.table("user_organizations")
        .select("role")
        .eq("user_id", user_id)
        .eq("org_id", project.data["org_id"])
        .execute()
    )
    if not member.data or member.data[0]["role"] not in roles:
        raise HTTPException(403, "Insufficient permissions")
    return project.data


class ManualMappingRequest(BaseModel):
    category: str
    fs_line_item: Optional[str] = None


@router.get("/{project_id}/mapping")
async def get_mapping(project_id: str, current_user: dict = Depends(get_current_user)):
    await _check_project_access(project_id, current_user["id"], roles=("admin", "auditor", "viewer"))
    result = (
        supabase.table("account_mappings")
        .select("*")
        .eq("project_id", project_id)
        .order("account_code")
        .execute()
    )
    return result.data or []


@router.post("/{project_id}/mapping/run")
async def run_mapping(project_id: str, current_user: dict = Depends(get_current_user)):
    """Trigger AI mapping — sync สำหรับตอนนี้ (Celery จะใส่ Phase 2)"""
    project = await _check_project_access(project_id, current_user["id"])

    # ดึง tb_rows ที่ยังไม่มี confirmed mapping
    tb_rows_resp = (
        supabase.table("tb_rows")
        .select("*")
        .eq("project_id", project_id)
        .order("row_order")
        .execute()
    )
    if not tb_rows_resp.data:
        raise HTTPException(400, "No TB rows found — upload file first")

    # แปลงเป็น TBRow objects
    rows = [
        TBRow(
            account_code=r["account_code"],
            account_name=r["account_name"],
            debit=Decimal(str(r["debit"])),
            credit=Decimal(str(r["credit"])),
            row_order=r["row_order"],
        )
        for r in tb_rows_resp.data
    ]

    # สร้าง job record
    job_resp = supabase.table("jobs").insert({
        "project_id": project_id,
        "job_type": "mapping",
        "status": "running",
        "total_rows": len(rows),
        "done_rows": 0,
        "progress": 0,
    }).execute()
    job_id = job_resp.data[0]["id"]

    try:
        results = await map_accounts(rows, project["org_id"])

        # บันทึก mapping results
        mapping_data = []
        for r in results:
            mapping_data.append({
                "project_id": project_id,
                "org_id": project["org_id"],
                "account_code": r.account_code,
                "category": r.category,
                "fs_line_item": r.fs_line_item,
                "confidence": float(r.confidence),
                "is_confirmed": r.confidence >= 0.8,
            })

        # Upsert ทีละ batch
        batch_size = 100
        for i in range(0, len(mapping_data), batch_size):
            supabase.table("account_mappings").upsert(
                mapping_data[i:i + batch_size],
                on_conflict="project_id,account_code"
            ).execute()

        # Update job → done
        supabase.table("jobs").update({
            "status": "done",
            "progress": 100,
            "done_rows": len(results),
        }).eq("id", job_id).execute()

        # Update project status → reviewing
        supabase.table("projects").update({"status": "reviewing"}).eq("id", project_id).execute()

        unmapped_count = sum(1 for r in results if r.confidence < 0.8)
        return {
            "job_id": job_id,
            "mapped": len(results),
            "needs_review": unmapped_count,
            "message": f"Mapping complete. {unmapped_count} rows need review.",
        }

    except Exception as e:
        supabase.table("jobs").update({
            "status": "failed",
            "error_msg": str(e),
        }).eq("id", job_id).execute()
        raise HTTPException(500, f"Mapping failed: {str(e)}")


@router.put("/{project_id}/mapping/{account_code}")
async def update_mapping(
    project_id: str,
    account_code: str,
    body: ManualMappingRequest,
    current_user: dict = Depends(get_current_user),
):
    project = await _check_project_access(project_id, current_user["id"])

    VALID_CATEGORIES = {
        "current_asset", "non_current_asset",
        "current_liability", "non_current_liability",
        "equity", "revenue", "cost_of_sales",
        "selling_expense", "admin_expense",
        "other_income", "other_expense",
        "operating_activity", "investing_activity", "financing_activity",
    }
    if body.category not in VALID_CATEGORIES:
        raise HTTPException(400, f"Invalid category: {body.category}")

    supabase.table("account_mappings").upsert({
        "project_id": project_id,
        "org_id": project["org_id"],
        "account_code": account_code,
        "category": body.category,
        "fs_line_item": body.fs_line_item,
        "confidence": 1.0,
        "is_confirmed": True,
        "confirmed_by": current_user["id"],
    }, on_conflict="project_id,account_code").execute()

    return {"message": "Mapping updated"}


@router.post("/{project_id}/mapping/confirm")
async def confirm_mapping(project_id: str, current_user: dict = Depends(get_current_user)):
    project = await _check_project_access(project_id, current_user["id"])

    # ตรวจว่ายังมี unmapped ไหม
    unmapped = (
        supabase.table("account_mappings")
        .select("account_code")
        .eq("project_id", project_id)
        .eq("is_confirmed", False)
        .execute()
    )
    if unmapped.data:
        codes = [r["account_code"] for r in unmapped.data[:5]]
        raise HTTPException(
            400,
            f"Still {len(unmapped.data)} unconfirmed rows: {', '.join(codes)}"
        )

    # Update project status
    supabase.table("projects").update({"status": "drafting"}).eq("id", project_id).execute()
    return {"message": "All mappings confirmed", "project_status": "drafting"}


@router.get("/{project_id}/mapping/unmapped")
async def get_unmapped(project_id: str, current_user: dict = Depends(get_current_user)):
    await _check_project_access(project_id, current_user["id"], roles=("admin", "auditor", "viewer"))
    result = (
        supabase.table("account_mappings")
        .select("*")
        .eq("project_id", project_id)
        .eq("is_confirmed", False)
        .order("account_code")
        .execute()
    )
    return result.data or []
