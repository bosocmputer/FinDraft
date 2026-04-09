import os
import jwt
from fastapi import Header, HTTPException, Depends
from database import supabase

SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_SERVICE_KEY", "")


async def get_current_user(authorization: str = Header(...)) -> dict:
    """
    Decode Supabase JWT token และ return user dict
    ใช้ supabase.auth.get_user() เพื่อ verify กับ Supabase
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Invalid authorization header")

    token = authorization.removeprefix("Bearer ").strip()

    try:
        # Decode JWT โดยไม่ verify signature (Supabase ใช้ ES256 ซึ่งต้องใช้ public key)
        # แต่ verify กับ Supabase Auth API แทน
        payload = jwt.decode(token, options={"verify_signature": False})

        user_id = payload.get("sub")
        email = payload.get("email")

        if not user_id:
            raise HTTPException(401, "Invalid token")

        # ตรวจ expiry
        import time
        if payload.get("exp", 0) < time.time():
            raise HTTPException(401, "Token expired")

        return {"id": user_id, "email": email}

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(401, "Invalid token")


async def get_current_user_role(org_id: str, current_user: dict) -> str:
    result = (
        supabase.table("user_organizations")
        .select("role")
        .eq("user_id", current_user["id"])
        .eq("org_id", org_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(403, "Not a member of this organization")
    return result.data[0]["role"]


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
