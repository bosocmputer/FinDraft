from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Literal, Optional
from database import supabase
from dependencies import get_current_user
from services.ai.draft_engine import run_draft, validate_financial_statements

router = APIRouter()

FSType = Literal["balance_sheet", "profit_loss", "cash_flow", "equity_changes", "audit_report"]


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


@router.post("/{project_id}/draft")
async def create_draft(project_id: str, current_user: dict = Depends(get_current_user)):
    project = await _check_project_access(project_id, current_user["id"])

    if project["status"] not in ("reviewing", "drafting"):
        raise HTTPException(400, f"Cannot draft from status: {project['status']} — confirm mapping first")

    try:
        result = await run_draft(project_id, project["org_id"], current_user["id"])
        return result
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Draft failed: {str(e)}")


@router.get("/{project_id}/fs/{fs_type}")
async def get_fs(
    project_id: str,
    fs_type: FSType,
    current_user: dict = Depends(get_current_user),
):
    await _check_project_access(project_id, current_user["id"], roles=("admin", "auditor", "viewer"))

    result = (
        supabase.table("financial_statements")
        .select("*")
        .eq("project_id", project_id)
        .eq("fs_type", fs_type)
        .order("version", desc=True)
        .limit(1)
        .execute()
    )
    if not result.data:
        raise HTTPException(404, f"No {fs_type} found — run draft first")
    return result.data[0]


@router.put("/{project_id}/fs/{fs_type}")
async def update_fs(
    project_id: str,
    fs_type: FSType,
    body: dict,
    current_user: dict = Depends(get_current_user),
):
    project = await _check_project_access(project_id, current_user["id"])

    if project["status"] == "finalized":
        raise HTTPException(400, "Cannot edit finalized statements")

    # ดึง fs ล่าสุด
    existing = (
        supabase.table("financial_statements")
        .select("*")
        .eq("project_id", project_id)
        .eq("fs_type", fs_type)
        .order("version", desc=True)
        .limit(1)
        .execute()
    )
    if not existing.data:
        raise HTTPException(404, f"No {fs_type} found")

    if existing.data[0]["is_final"]:
        raise HTTPException(400, "Statement is finalized — cannot edit")

    new_version = existing.data[0]["version"] + 1
    result = supabase.table("financial_statements").insert({
        "project_id": project_id,
        "fs_type": fs_type,
        "data": body,
        "version": new_version,
        "is_final": False,
        "created_by": current_user["id"],
    }).execute()

    return result.data[0]


@router.post("/{project_id}/fs/{fs_type}/finalize")
async def finalize_fs(
    project_id: str,
    fs_type: FSType,
    current_user: dict = Depends(get_current_user),
):
    project = await _check_project_access(project_id, current_user["id"], roles=("admin",))

    # ดึง fs ทั้งหมดล่าสุด
    fs_types = ["balance_sheet", "profit_loss", "cash_flow", "equity_changes"]
    fs_data = {}
    for ft in fs_types:
        r = (
            supabase.table("financial_statements")
            .select("*")
            .eq("project_id", project_id)
            .eq("fs_type", ft)
            .order("version", desc=True)
            .limit(1)
            .execute()
        )
        if not r.data:
            raise HTTPException(400, f"Missing {ft} — run draft first")
        fs_data[ft] = r.data[0]["data"]

    # Validate 5 เงื่อนไข (server-side)
    from services.ai.draft_engine import validate_financial_statements
    validation = validate_financial_statements(
        fs_data["balance_sheet"],
        fs_data["profit_loss"],
        fs_data["cash_flow"],
        fs_data["equity_changes"],
        project_id,
    )
    if not validation.is_valid:
        raise HTTPException(400, {"errors": validation.errors})

    # Mark is_final = true สำหรับ version ล่าสุดของทุก fs_type
    for ft in fs_types:
        r = (
            supabase.table("financial_statements")
            .select("id")
            .eq("project_id", project_id)
            .eq("fs_type", ft)
            .order("version", desc=True)
            .limit(1)
            .execute()
        )
        if r.data:
            supabase.table("financial_statements").update(
                {"is_final": True}
            ).eq("id", r.data[0]["id"]).execute()

    # Update project status → finalized
    supabase.table("projects").update({"status": "finalized"}).eq("id", project_id).execute()

    return {"message": "Finalized successfully", "project_status": "finalized"}


@router.get("/{project_id}/fs/{fs_type}/versions")
async def get_fs_versions(
    project_id: str,
    fs_type: FSType,
    current_user: dict = Depends(get_current_user),
):
    await _check_project_access(project_id, current_user["id"], roles=("admin", "auditor", "viewer"))
    result = (
        supabase.table("financial_statements")
        .select("id, version, is_final, created_at, created_by")
        .eq("project_id", project_id)
        .eq("fs_type", fs_type)
        .order("version", desc=True)
        .execute()
    )
    return result.data or []
