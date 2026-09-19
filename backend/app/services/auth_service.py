"""
Auth service — phone-based OTP registration and JWT token management.

OTP delivery is abstracted; in development mode, a fixed configurable
code is used. Real SMS integration is provider-pluggable.

LLM and external AI are never involved in authentication.
"""
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.user import User
from app.models.shop_member import ShopMember
from app.models.enums import UserRole, MembershipStatus
from app.schemas.common import ErrorDetail

settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# In-memory OTP store (dev only — production would use Redis or SMS provider)
_otp_store: dict[str, tuple[str, datetime]] = {}

ALGORITHM = "HS256"


# ── OTP ───────────────────────────────────────────────────────────────────────

def generate_otp(phone: str) -> str:
    """Generate and store OTP for phone. Returns OTP for dev use."""
    if settings.SAATHI_OTP_DEV_MODE:
        otp = settings.SAATHI_OTP_DEV_CODE
    else:
        otp = str(secrets.randbelow(900000) + 100000)  # 6-digit
    expires = datetime.now(timezone.utc) + timedelta(minutes=10)
    _otp_store[phone] = (otp, expires)
    return otp


def verify_otp(phone: str, otp: str) -> bool:
    """Verify OTP. Returns True if valid and not expired."""
    if phone not in _otp_store:
        return False
    stored_otp, expires = _otp_store[phone]
    if datetime.now(timezone.utc) > expires:
        del _otp_store[phone]
        return False
    if stored_otp != otp:
        return False
    del _otp_store[phone]
    return True


# ── JWT ───────────────────────────────────────────────────────────────────────

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


# ── User CRUD ─────────────────────────────────────────────────────────────────

async def get_user_by_phone(db: AsyncSession, phone: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.phone == phone))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id) -> Optional[User]:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, name: str, phone: str) -> User:
    user = User(name=name, phone=phone, is_active=True, is_phone_verified=False)
    db.add(user)
    await db.flush()
    return user


async def get_user_shops(db: AsyncSession, user_id) -> list[ShopMember]:
    result = await db.execute(
        select(ShopMember).where(
            ShopMember.user_id == user_id,
            ShopMember.status == MembershipStatus.ACTIVE,
        )
    )
    return result.scalars().all()
