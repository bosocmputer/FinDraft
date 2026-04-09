from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Literal

router = APIRouter()


class CreateOrgRequest(BaseModel):
    name: str


class InviteRequest(BaseModel):
    email: EmailStr
    role: Literal["admin", "auditor", "viewer"]


class UpdateMemberRoleRequest(BaseModel):
    role: Literal["admin", "auditor", "viewer"]


@router.get("")
async def list_orgs():
    # TODO: list orgs ที่ current user อยู่
    raise HTTPException(501, "Not implemented")


@router.post("")
async def create_org(body: CreateOrgRequest):
    # TODO: สร้าง org ใหม่ + add creator เป็น admin
    raise HTTPException(501, "Not implemented")


@router.get("/{org_id}/members")
async def list_members(org_id: str):
    # TODO: list members ของ org
    raise HTTPException(501, "Not implemented")


@router.put("/{org_id}/members/{user_id}")
async def update_member_role(org_id: str, user_id: str, body: UpdateMemberRoleRequest):
    # TODO: เปลี่ยน role — admin only
    raise HTTPException(501, "Not implemented")


@router.delete("/{org_id}/members/{user_id}")
async def remove_member(org_id: str, user_id: str):
    # TODO: ลบ member ออกจาก org — admin only
    raise HTTPException(501, "Not implemented")


# --- Invite flow ---

@router.post("/{org_id}/invitations")
async def create_invitation(org_id: str, body: InviteRequest):
    # TODO: สร้าง invite token, บันทึกลง invitations table, ส่ง email
    raise HTTPException(501, "Not implemented")


@router.get("/{org_id}/invitations")
async def list_invitations(org_id: str):
    # TODO: list pending invitations — admin only
    raise HTTPException(501, "Not implemented")


@router.delete("/{org_id}/invitations/{invitation_id}")
async def cancel_invitation(org_id: str, invitation_id: str):
    # TODO: ยกเลิก invite — admin only
    raise HTTPException(501, "Not implemented")
