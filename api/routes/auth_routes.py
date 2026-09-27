from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
from utils.auth import DEMO_USER, login_user, register_user, get_supabase_auth_client

router = APIRouter(prefix="/api/auth", tags=["auth"])

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str

@router.post("/demo")
def demo_login():
    return {
        "success": True,
        "user": DEMO_USER,
        "token": "demo-token"
    }

@router.post("/login")
def login(req: LoginRequest):
    success, msg = login_user(req.email, req.password)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {
        "success": True,
        "message": msg,
        "user": {"email": req.email, "is_demo": False}
    }

@router.post("/register")
def register(req: RegisterRequest):
    success, msg = register_user(req.email, req.password, req.full_name)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {
        "success": True,
        "message": msg
    }
