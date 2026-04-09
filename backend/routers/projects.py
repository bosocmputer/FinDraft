from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from database import supabase
from dependencies import get_current_user, require_role

router = APIRouter()


class CreateProjectRequest(BaseModel):
    org_id: str
    company_name: str
    fiscal_year: int
    comparative_year: Optional[int] = None
    currency: str = "THB"
    template_id: Optional[str] = None


class UpdateProjectRequest(BaseModel):
    company_name: Optional[str] = None
    fiscal_year: Optional[int] = None
    comparative_year: Optional[int] = None
    currency: Optional[str] = None


@router.get("")
async def list_projects(org_id: str, current_user: dict = Depends(get_current_user)):
    # ตรวจว่า user อยู่ใน org นี้
    member = (
        supabase.table("user_organizations")
        .select("role")
        .eq("user_id", current_user["id"])
        .eq("org_id", org_id)
        .execute()
    )
    if not member.data:
        raise HTTPException(403, "Not a member of this organization")

    result = (
        supabase.table("projects")
        .select("*")
        .eq("org_id", org_id)
        .is_("deleted_at", "null")
        .order("created_at", desc=True)
        .execute()
    )
    return result.data or []


@router.post("")
async def create_project(
    body: CreateProjectRequest,
    current_user: dict = Depends(get_current_user),
):
    # ตรวจ member
    member = (
        supabase.table("user_organizations")
        .select("role")
        .eq("user_id", current_user["id"])
        .eq("org_id", body.org_id)
        .execute()
    )
    if not member.data or member.data[0]["role"] not in ("admin", "auditor"):
        raise HTTPException(403, "Insufficient permissions")

    data = {
        "org_id": body.org_id,
        "company_name": body.company_name,
        "fiscal_year": body.fiscal_year,
        "currency": body.currency,
        "status": "uploading",
        "created_by": current_user["id"],
    }
    if body.comparative_year:
        data["comparative_year"] = body.comparative_year
    if body.template_id:
        data["template_id"] = body.template_id

    result = supabase.table("projects").insert(data).execute()
    if not result.data:
        raise HTTPException(500, "Failed to create project")

    return result.data[0]


@router.get("/{project_id}")
async def get_project(project_id: str, current_user: dict = Depends(get_current_user)):
    result = (
        supabase.table("projects")
        .select("*")
        .eq("id", project_id)
        .is_("deleted_at", "null")
        .single()
        .execute()
    )
    if not result.data:
        raise HTTPException(404, "Project not found")

    # ตรวจว่า user อยู่ใน org ของ project นี้
    member = (
        supabase.table("user_organizations")
        .select("role")
        .eq("user_id", current_user["id"])
        .eq("org_id", result.data["org_id"])
        .execute()
    )
    if not member.data:
        raise HTTPException(403, "Access denied")

    return result.data


@router.put("/{project_id}")
async def update_project(
    project_id: str,
    body: UpdateProjectRequest,
    current_user: dict = Depends(get_current_user),
):
    project = await get_project(project_id, current_user)

    member = (
        supabase.table("user_organizations")
        .select("role")
        .eq("user_id", current_user["id"])
        .eq("org_id", project["org_id"])
        .execute()
    )
    if not member.data or member.data[0]["role"] not in ("admin", "auditor"):
        raise HTTPException(403, "Insufficient permissions")

    if project.get("status") == "finalized":
        raise HTTPException(400, "Cannot edit a finalized project")

    updates = body.model_dump(exclude_none=True)
    if not updates:
        return project

    result = supabase.table("projects").update(updates).eq("id", project_id).execute()
    return result.data[0]


@router.delete("/{project_id}")
async def delete_project(project_id: str, current_user: dict = Depends(get_current_user)):
    project = await get_project(project_id, current_user)

    member = (
        supabase.table("user_organizations")
        .select("role")
        .eq("user_id", current_user["id"])
        .eq("org_id", project["org_id"])
        .execute()
    )
    if not member.data or member.data[0]["role"] != "admin":
        raise HTTPException(403, "Only admin can delete projects")

    now = datetime.now(timezone.utc).isoformat()
    supabase.table("projects").update({"deleted_at": now}).eq("id", project_id).execute()
    return {"message": "Project deleted"}


@router.post("/{project_id}/restore")
async def restore_project(project_id: str, current_user: dict = Depends(get_current_user)):
    result = (
        supabase.table("projects")
        .select("*")
        .eq("id", project_id)
        .single()
        .execute()
    )
    if not result.data:
        raise HTTPException(404, "Project not found")

    member = (
        supabase.table("user_organizations")
        .select("role")
        .eq("user_id", current_user["id"])
        .eq("org_id", result.data["org_id"])
        .execute()
    )
    if not member.data or member.data[0]["role"] != "admin":
        raise HTTPException(403, "Only admin can restore projects")

    supabase.table("projects").update({"deleted_at": None}).eq("id", project_id).execute()
    return {"message": "Project restored"}
