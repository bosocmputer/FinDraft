from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import supabase

router = APIRouter()


class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/register")
async def register(body: RegisterRequest):
    try:
        # สร้าง user ใน Supabase Auth
        auth_resp = supabase.auth.sign_up({
            "email": body.email,
            "password": body.password,
        })
        if not auth_resp.user:
            raise HTTPException(400, "Registration failed")

        user_id = auth_resp.user.id

        # Insert ลง users table
        supabase.table("users").upsert({
            "id": user_id,
            "email": body.email,
            "name": body.name,
        }).execute()

        return {
            "user_id": user_id,
            "email": body.email,
            "access_token": auth_resp.session.access_token if auth_resp.session else None,
        }
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
