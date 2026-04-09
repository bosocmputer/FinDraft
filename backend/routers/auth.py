from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from database import supabase

router = APIRouter()


class RegisterRequest(BaseModel):
    email: str
    org_name: str


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/register")
async def register(body: RegisterRequest, authorization: str = Header(None)):
    """
    Called after Supabase Auth signup — creates user profile + org.
    Requires Bearer token from Supabase session (passed by frontend).
    """
    from dependencies import _decode_token
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]

    if not token:
        raise HTTPException(401, "Authorization token required")

    payload = _decode_token(token)
    user_id = payload.get("sub")
    email = payload.get("email", body.email)

    if not user_id:
        raise HTTPException(401, "Invalid token")

    try:
        # Upsert user profile
        supabase.table("users").upsert({
            "id": user_id,
            "email": email,
            "name": email.split("@")[0],
        }).execute()

        # สร้าง org ใหม่
        org = supabase.table("organizations").insert({"name": body.org_name}).execute()
        if not org.data:
            raise HTTPException(500, "Failed to create organization")
        org_id = org.data[0]["id"]

        # Add user เป็น admin ของ org
        supabase.table("user_organizations").insert({
            "user_id": user_id,
            "org_id": org_id,
            "role": "admin",
        }).execute()

        return {"user_id": user_id, "org_id": org_id, "org_name": body.org_name}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, str(e))


@router.post("/login")
async def login(body: LoginRequest):
    try:
        auth_resp = supabase.auth.sign_in_with_password({
            "email": body.email,
            "password": body.password,
        })
        if not auth_resp.user or not auth_resp.session:
            raise HTTPException(401, "Invalid credentials")

        # ดึง orgs ที่ user อยู่
        orgs_resp = (
            supabase.table("user_organizations")
            .select("org_id, role, organizations(id, name)")
            .eq("user_id", auth_resp.user.id)
            .execute()
        )

        return {
            "access_token": auth_resp.session.access_token,
            "refresh_token": auth_resp.session.refresh_token,
            "user": {
                "id": auth_resp.user.id,
                "email": auth_resp.user.email,
            },
            "organizations": orgs_resp.data or [],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(401, str(e))


@router.post("/logout")
async def logout(authorization: str = None):
    try:
        supabase.auth.sign_out()
        return {"message": "Logged out"}
    except Exception:
        return {"message": "Logged out"}


@router.post("/refresh")
async def refresh_token(refresh_token: str):
    try:
        resp = supabase.auth.refresh_session(refresh_token)
        if not resp.session:
            raise HTTPException(401, "Invalid refresh token")
        return {
            "access_token": resp.session.access_token,
            "refresh_token": resp.session.refresh_token,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(401, str(e))
