import uuid
from datetime import datetime
from pydantic import BaseModel, field_validator
import re


class UserBase(BaseModel):
    name: str
    phone: str

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        # Basic E.164 check — full validation deferred to auth service
        if not re.match(r"^\+[1-9]\d{6,14}$", v):
            raise ValueError("Phone must be in E.164 format, e.g. +919876543210")
        return v


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    name: str | None = None
    is_active: bool | None = None


class UserResponse(UserBase):
    id: uuid.UUID
    is_active: bool
    is_phone_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
