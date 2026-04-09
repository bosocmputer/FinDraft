import os
from fastapi import Header, HTTPException, Depends
from supabase import create_client
from database import supabase

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")


async def get_current_user(authorization: str = Header(...)) -> dict:
    """
    ตรวจ JWT token จาก Supabase Auth
    Return user dict: { id, email, ... }
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Invalid authorization header")

    token = authorization.removeprefix("Bearer ").strip()

    try:
        response = supabase.auth.get_user(token)
        if not response or not response.user:
            raise HTTPException(401, "Invalid or expired token")
        return {"id": response.user.id, "email": response.user.email}
    except Exception:
        raise HTTPException(401, "Invalid or expired token")


async def get_current_user_role(
    org_id: str,
    current_user: dict = Depends(get_current_user),
) -> str:
    """Return role ของ user ใน org นั้น"""
    result = (
        supabase.table("user_organizations")
        .select("role")
        .eq("user_id", current_user["id"])
        .eq("org_id", org_id)
        .single()
        .execute()
    )
    if not result.data:
        raise HTTPException(403, "Not a member of this organization")
    return result.data["role"]


def require_role(*roles: str):
    """Dependency factory — ตรวจ role ก่อนเข้า endpoint"""
    async def check(
        org_id: str,
        current_user: dict = Depends(get_current_user),
    ) -> dict:
        role = await get_current_user_role(org_id, current_user)
        if role not in roles:
            raise HTTPException(403, f"Requires role: {', '.join(roles)}")
        current_user["role"] = role
        current_user["org_id"] = org_id
        return current_user
    return check
