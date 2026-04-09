from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Literal, Optional

router = APIRouter()


class SetProviderRequest(BaseModel):
    provider: Literal["anthropic", "openai", "gemini", "openrouter"]
    model: str
    api_key: str  # plaintext — encrypt ก่อนบันทึกลง DB


@router.get("/{org_id}/ai-provider")
async def get_ai_provider(org_id: str):
    # TODO: ดึง provider config (ไม่ return api_key)
    raise HTTPException(501, "Not implemented")


@router.put("/{org_id}/ai-provider")
async def set_ai_provider(org_id: str, body: SetProviderRequest):
    # TODO: encrypt api_key ด้วย AES-256-GCM → บันทึกลง org_ai_configs — admin only
    raise HTTPException(501, "Not implemented")


@router.delete("/{org_id}/ai-provider")
async def delete_ai_provider(org_id: str):
    # TODO: ลบ config → fallback เป็น system default Anthropic
    raise HTTPException(501, "Not implemented")


@router.get("/{org_id}/ai-provider/test")
async def test_ai_provider(org_id: str):
    """
    ทดสอบว่า API key ใช้งานได้
    Rate limit: 5/minute per org+user
    """
    # TODO: ดึง provider config → เรียก provider.complete() ด้วย prompt ง่ายๆ
    raise HTTPException(501, "Not implemented")
