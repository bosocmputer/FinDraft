from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class CreateTemplateRequest(BaseModel):
    org_id: str
    name: str
    description: Optional[str] = None


@router.get("")
async def list_templates(org_id: str):
    # TODO: list templates ของ org
    raise HTTPException(501, "Not implemented")


@router.post("")
async def create_template(body: CreateTemplateRequest):
    # TODO: สร้าง template ใหม่
    raise HTTPException(501, "Not implemented")


@router.get("/{template_id}")
async def get_template(template_id: str):
    raise HTTPException(501, "Not implemented")


@router.put("/{template_id}")
async def update_template(template_id: str):
    raise HTTPException(501, "Not implemented")


@router.delete("/{template_id}")
async def delete_template(template_id: str):
    raise HTTPException(501, "Not implemented")


@router.post("/{template_id}/clone")
async def clone_template(template_id: str):
    # TODO: clone template (สำหรับปีบัญชีใหม่หรือ org อื่น)
    raise HTTPException(501, "Not implemented")
