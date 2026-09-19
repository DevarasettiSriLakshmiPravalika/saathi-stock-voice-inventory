"""
FastAPI dependencies: authenticated user, role enforcement, shop isolation.
"""
import uuid
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.models.shop import Shop
from app.models.shop_member import ShopMember
from app.models.enums import UserRole, MembershipStatus
from app.services import auth_service

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = credentials.credentials
    payload = auth_service.decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTH_INVALID", "message": "Invalid or expired token."},
        )
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTH_INVALID", "message": "Token missing subject."},
        )
    user = await auth_service.get_user_by_id(db, uuid.UUID(user_id))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTH_INVALID", "message": "User not found or inactive."},
        )
    return user


async def get_shop_or_404(shop_id: uuid.UUID, db: AsyncSession) -> Shop:
    result = await db.execute(select(Shop).where(Shop.id == shop_id))
    shop = result.scalar_one_or_none()
    if not shop or not shop.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Shop not found."},
        )
    return shop


async def require_shop_owner(
    shop_id: uuid.UUID,
    current_user: User,
    db: AsyncSession,
) -> ShopMember:
    """Raises 403 if current_user is not an active OWNER of the shop."""
    result = await db.execute(
        select(ShopMember).where(
            ShopMember.shop_id == shop_id,
            ShopMember.user_id == current_user.id,
            ShopMember.role == UserRole.OWNER,
            ShopMember.status == MembershipStatus.ACTIVE,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "Owner access required."},
        )
    return member


async def require_shop_member(
    shop_id: uuid.UUID,
    current_user: User,
    db: AsyncSession,
) -> ShopMember:
    """Raises 403 if current_user is not an active member of the shop."""
    result = await db.execute(
        select(ShopMember).where(
            ShopMember.shop_id == shop_id,
            ShopMember.user_id == current_user.id,
            ShopMember.status == MembershipStatus.ACTIVE,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "Shop membership required."},
        )
    return member


def error_response(code: str, message: str, status_code: int = 400):
    raise HTTPException(
        status_code=status_code,
        detail={"code": code, "message": message},
    )
