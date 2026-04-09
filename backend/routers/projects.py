from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

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
async def list_projects(org_id: str):
    # TODO: list projects ของ org (ไม่รวม deleted_at IS NOT NULL)
    raise HTTPException(501, "Not implemented")


@router.post("")
async def create_project(body: CreateProjectRequest):
    # TODO: สร้าง project ใหม่
    raise HTTPException(501, "Not implemented")


@router.get("/{project_id}")
async def get_project(project_id: str):
    # TODO: ดึง project โดย id
    raise HTTPException(501, "Not implemented")


@router.put("/{project_id}")
async def update_project(project_id: str, body: UpdateProjectRequest):
    # TODO: แก้ไข project
    raise HTTPException(501, "Not implemented")


@router.delete("/{project_id}")
async def delete_project(project_id: str):
    # TODO: soft delete — set deleted_at = now()
    raise HTTPException(501, "Not implemented")


@router.post("/{project_id}/restore")
async def restore_project(project_id: str):
    # TODO: กู้คืน soft-deleted project — set deleted_at = NULL
    raise HTTPException(501, "Not implemented")
