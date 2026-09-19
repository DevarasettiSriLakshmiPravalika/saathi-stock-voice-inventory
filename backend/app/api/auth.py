"""
Auth API routes — registration, OTP verification, token refresh, and profile.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, field_validator
import re

from app.database import get_db
from app.models.user import User
from app.schemas.common import SuccessResponse
from app.schemas.user import UserResponse
from app.services import auth_service
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    name: str
    phone: str

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not re.match(r"^\+[1-9]\d{6,14}$", v):
            raise ValueError("Phone must be in E.164 format, e.g. +919876543210")
        return v


class LoginRequest(BaseModel):
    phone: str

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not re.match(r"^\+[1-9]\d{6,14}$", v):
            raise ValueError("Phone must be in E.164 format, e.g. +919876543210")
        return v


class VerifyRequest(BaseModel):
    phone: str
    otp: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


@router.post("/register")
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    Register a new user by phone number.
    Sends OTP (dev mode: fixed OTP, production: SMS).
    """
    existing = await auth_service.get_user_by_phone(db, body.phone)
    if existing and existing.is_phone_verified:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "DUPLICATE_PHONE", "message": "Phone number already registered."},
        )

    if not existing:
        user = await auth_service.create_user(db, body.name, body.phone)
        await db.commit()
        await db.refresh(user)
    else:
        # Allow re-registration if not yet verified
        user = existing

    otp = auth_service.generate_otp(body.phone)

    # In production, send OTP via SMS here
    # For dev, the OTP is returned in the response (never do this in production)
    from app.config import get_settings
    s = get_settings()

    response_data = {
        "message": "OTP sent. Verify to complete registration.",
        "phone": body.phone,
    }
    if s.SAATHI_OTP_DEV_MODE:
        response_data["dev_otp"] = otp  # Only in dev mode

    return {"success": True, "data": response_data}


@router.post("/login")
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Request OTP for an existing registered user to log in.
    """
    user = await auth_service.get_user_by_phone(db, body.phone)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "USER_NOT_FOUND", "message": "Phone number not registered. Please sign up first."},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "USER_INACTIVE", "message": "Account is deactivated."},
        )

    otp = auth_service.generate_otp(body.phone)
    from app.config import get_settings
    s = get_settings()

    response_data = {
        "message": "OTP sent. Verify to complete login.",
        "phone": body.phone,
        "name": user.name,
    }
    if s.SAATHI_OTP_DEV_MODE:
        response_data["dev_otp"] = otp

    return {"success": True, "data": response_data}


@router.post("/verify")
async def verify(body: VerifyRequest, db: AsyncSession = Depends(get_db)):
    """
    Verify OTP and return JWT access + refresh tokens.
    """
    user = await auth_service.get_user_by_phone(db, body.phone)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Phone number not registered."},
        )

    if not auth_service.verify_otp(body.phone, body.otp):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTH_INVALID", "message": "Invalid or expired OTP."},
        )

    # Mark phone as verified
    user.is_phone_verified = True
    await db.commit()
    await db.refresh(user)

    token_data = {"sub": str(user.id)}
    access_token = auth_service.create_access_token(token_data)
    refresh_token = auth_service.create_refresh_token(token_data)

    return {
        "success": True,
        "data": {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "name": user.name,
                "phone": user.phone,
                "is_active": user.is_active,
                "is_phone_verified": user.is_phone_verified,
                "created_at": user.created_at.isoformat(),
                "updated_at": user.updated_at.isoformat(),
            },
        },
    }


@router.post("/refresh")
async def refresh_token(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """
    Exchange a refresh token for a new access token.
    """
    import uuid
    payload = auth_service.decode_token(body.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTH_INVALID", "message": "Invalid or expired refresh token."},
        )
    user_id = payload.get("sub")
    user = await auth_service.get_user_by_id(db, uuid.UUID(user_id))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTH_INVALID", "message": "User not found."},
        )

    token_data = {"sub": str(user.id)}
    access_token = auth_service.create_access_token(token_data)
    new_refresh_token = auth_service.create_refresh_token(token_data)

    return {
        "success": True,
        "data": {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        },
    }
