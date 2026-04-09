from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

router = APIRouter()


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/register")
async def register(body: RegisterRequest):
    # TODO: Supabase Auth — create user + insert into users table
    raise HTTPException(501, "Not implemented — wire Supabase Auth")


@router.post("/login")
async def login(body: LoginRequest):
    # TODO: Supabase Auth — sign in, return JWT
    raise HTTPException(501, "Not implemented — wire Supabase Auth")
