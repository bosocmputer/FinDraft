import secrets
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Literal
from database import supabase
from dependencies import get_current_user, require_role

router = APIRouter()


class CreateOrgRequest(BaseModel):
    name: str


class InviteRequest(BaseModel):
    email: str
    role: Literal["admin", "auditor", "viewer"]


class UpdateMemberRoleRequest(BaseModel):
    role: Literal["admin", "auditor", "viewer"]


class AcceptInviteRequest(BaseModel):
    token: str


# ==========================================
# Organizations
# ==========================================

@router.get("")
async def list_orgs(current_user: dict = Depends(get_current_user)):
    result = (
        supabase.table("user_organizations")
        .select("role, joined_at, organizations(id, name, created_at)")
        .eq("user_id", current_user["id"])
        .execute()
    )
    # Flatten nested structure: { organizations: {id, name} } → {id, name, role}
    orgs = []
    for row in (result.data or []):
        org = row.get("organizations") or {}
        if org:
            orgs.append({
                "id": org["id"],
                "name": org["name"],
                "created_at": org.get("created_at"),
                "role": row["role"],
            })
    return orgs


@router.post("")
async def create_org(body: CreateOrgRequest, current_user: dict = Depends(get_current_user)):
    # สร้าง org
    org = supabase.table("organizations").insert({"name": body.name}).execute()
    if not org.data:
        raise HTTPException(500, "Failed to create organization")

    org_id = org.data[0]["id"]

    # Add creator เป็น admin
    supabase.table("user_organizations").insert({
        "user_id": current_user["id"],
        "org_id": org_id,
        "role": "admin",
    }).execute()

    return org.data[0]


# ==========================================
# Members
# ==========================================

@router.get("/{org_id}/members")
async def list_members(
    org_id: str,
    current_user: dict = Depends(require_role("admin", "auditor", "viewer")),
):
    result = (
        supabase.table("user_organizations")
        .select("user_id, role, joined_at, users(id, email, name)")
        .eq("org_id", org_id)
        .execute()
    )
    return result.data or []


@router.put("/{org_id}/members/{user_id}")
async def update_member_role(
    org_id: str,
    user_id: str,
    body: UpdateMemberRoleRequest,
    current_user: dict = Depends(require_role("admin")),
):
    if user_id == current_user["id"]:
        raise HTTPException(400, "Cannot change your own role")

    supabase.table("user_organizations").update(
        {"role": body.role}
    ).eq("org_id", org_id).eq("user_id", user_id).execute()

    return {"message": "Role updated"}


@router.delete("/{org_id}/members/{user_id}")
async def remove_member(
    org_id: str,
    user_id: str,
    current_user: dict = Depends(require_role("admin")),
):
    if user_id == current_user["id"]:
        raise HTTPException(400, "Cannot remove yourself")

    supabase.table("user_organizations").delete().eq(
        "org_id", org_id
    ).eq("user_id", user_id).execute()

    return {"message": "Member removed"}


# ==========================================
# Invitations
# ==========================================

@router.post("/{org_id}/invitations")
async def create_invitation(
    org_id: str,
    body: InviteRequest,
    current_user: dict = Depends(require_role("admin")),
):
    # ตรวจว่า email นี้อยู่ใน org แล้วหรือยัง
    existing_user = supabase.table("users").select("id").eq("email", body.email).execute()
    if existing_user.data:
        uid = existing_user.data[0]["id"]
        already = (
            supabase.table("user_organizations")
            .select("user_id")
            .eq("org_id", org_id)
            .eq("user_id", uid)
            .execute()
        )
        if already.data:
            raise HTTPException(400, "User is already a member")

    token = secrets.token_urlsafe(32)
    expires_at = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()

    result = supabase.table("invitations").insert({
        "org_id": org_id,
        "email": body.email,
        "role": body.role,
        "token": token,
        "invited_by": current_user["id"],
        "expires_at": expires_at,
        "status": "pending",
    }).execute()

    invite_link = f"http://localhost:3000/invite?token={token}"
    return {**result.data[0], "invite_link": invite_link}


@router.get("/{org_id}/invitations")
async def list_invitations(
    org_id: str,
    current_user: dict = Depends(require_role("admin")),
):
    result = (
        supabase.table("invitations")
        .select("*")
        .eq("org_id", org_id)
        .eq("status", "pending")
        .execute()
    )
    return result.data or []


@router.delete("/{org_id}/invitations/{invitation_id}")
async def cancel_invitation(
    org_id: str,
    invitation_id: str,
    current_user: dict = Depends(require_role("admin")),
):
    supabase.table("invitations").update(
        {"status": "expired"}
    ).eq("id", invitation_id).eq("org_id", org_id).execute()
    return {"message": "Invitation cancelled"}


# ==========================================
# Accept Invite (public endpoint)
# ==========================================

@router.post("/invitations/accept")
async def accept_invitation(
    body: AcceptInviteRequest,
    current_user: dict = Depends(get_current_user),
):
    now = datetime.now(timezone.utc).isoformat()

    invite = (
        supabase.table("invitations")
        .select("*")
        .eq("token", body.token)
        .eq("status", "pending")
        .single()
        .execute()
    )
    if not invite.data:
        raise HTTPException(404, "Invalid or expired invitation")

    if invite.data["expires_at"] < now:
        supabase.table("invitations").update({"status": "expired"}).eq(
            "token", body.token
        ).execute()
        raise HTTPException(400, "Invitation has expired")

    # Add user เข้า org
    supabase.table("user_organizations").upsert({
        "user_id": current_user["id"],
        "org_id": invite.data["org_id"],
        "role": invite.data["role"],
        "invited_by": invite.data["invited_by"],
    }).execute()

    # Mark invite accepted
    supabase.table("invitations").update({
        "status": "accepted",
        "accepted_at": now,
    }).eq("token", body.token).execute()

    return {"message": "Joined organization", "org_id": invite.data["org_id"]}
