from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class ManualMappingRequest(BaseModel):
    category: str
    fs_line_item: Optional[str] = None


@router.get("/{project_id}/mapping")
async def get_mapping(project_id: str):
    # TODO: ดึง account_mappings ของ project
    raise HTTPException(501, "Not implemented")


@router.post("/{project_id}/mapping/run")
async def run_mapping(project_id: str):
    """
    Trigger AI mapper → Celery async task
    Returns { job_id } ทันที
    Rate limit: 10/minute per org+user
    """
    # TODO: dispatch Celery mapping task, บันทึก job, return job_id
    raise HTTPException(501, "Not implemented")


@router.put("/{project_id}/mapping/{account_code}")
async def update_mapping(project_id: str, account_code: str, body: ManualMappingRequest):
    # TODO: แก้ mapping manual + set is_confirmed=true
    raise HTTPException(501, "Not implemented")


@router.post("/{project_id}/mapping/confirm")
async def confirm_mapping(project_id: str):
    # TODO: confirm ทั้ง batch → is_confirmed=true ทุก row, update project status → 'reviewing'
    raise HTTPException(501, "Not implemented")


@router.get("/{project_id}/mapping/unmapped")
async def get_unmapped(project_id: str):
    # TODO: rows ที่ confidence < 0.8 หรือ is_confirmed=false
    raise HTTPException(501, "Not implemented")
