from fastapi import APIRouter, HTTPException
from typing import Literal

router = APIRouter()

FSType = Literal["balance_sheet", "profit_loss", "cash_flow", "equity_changes", "audit_report"]


@router.post("/{project_id}/draft")
async def run_draft(project_id: str):
    """
    สร้างงบการเงินครบชุด (BS + P&L + CF + SCE)
    Rate limit: 5/minute per org+user
    """
    # TODO: เรียก draft_engine.py, validate 5 เงื่อนไข, บันทึก financial_statements
    raise HTTPException(501, "Not implemented")


@router.get("/{project_id}/fs/{fs_type}")
async def get_fs(project_id: str, fs_type: FSType):
    # TODO: ดึง financial statement ล่าสุด
    raise HTTPException(501, "Not implemented")


@router.put("/{project_id}/fs/{fs_type}")
async def update_fs(project_id: str, fs_type: FSType):
    # TODO: แก้ไขงบ (inline edit) + บันทึก version ใหม่
    raise HTTPException(501, "Not implemented")


@router.post("/{project_id}/fs/{fs_type}/finalize")
async def finalize_fs(project_id: str, fs_type: FSType):
    """
    Finalize งบ — admin only
    validate 5 เงื่อนไขอีกรอบ (server-side)
    """
    # TODO: validate + set is_final=true + project status → 'finalized'
    raise HTTPException(501, "Not implemented")


@router.get("/{project_id}/fs/{fs_type}/versions")
async def get_fs_versions(project_id: str, fs_type: FSType):
    # TODO: version history ของงบ
    raise HTTPException(501, "Not implemented")
