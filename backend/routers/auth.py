"""
Aspire English Hub - Auth Router
==================================
Authentication endpoints: signup, login, logout, token refresh.
"""

from fastapi import APIRouter, Depends
from models.schemas import SignupRequest, LoginRequest, PasswordResetRequest, ProfileUpdate
from services.auth_service import auth_service
from middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/signup")
async def signup(req: SignupRequest):
    return await auth_service.signup(req.email, req.password, req.full_name, req.display_name)


@router.post("/login")
async def login(req: LoginRequest):
    return await auth_service.login(req.email, req.password)


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    return await auth_service.logout(current_user.get("token", ""))


@router.post("/refresh")
async def refresh_token(refresh_token: str):
    return await auth_service.refresh_token(refresh_token)


@router.post("/reset-password")
async def reset_password(req: PasswordResetRequest):
    return await auth_service.reset_password(req.email)


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return await auth_service.get_profile(current_user["id"])


@router.put("/me")
async def update_me(updates: ProfileUpdate, current_user: dict = Depends(get_current_user)):
    return await auth_service.update_profile(current_user["id"], updates.model_dump(exclude_none=True))
