import uuid
from datetime import datetime
from pydantic import BaseModel, field_validator
from app.models.enums import UserRole, MembershipStatus


class ShopMemberBase(BaseModel):
    role: UserRole


class ShopMemberCreate(ShopMemberBase):
    """Used when owner adds a member — phone is used to look up/create the user."""
    name: str
    phone: str

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: UserRole) -> UserRole:
        if v == UserRole.OWNER:
            raise ValueError("Cannot assign OWNER role via member creation. Only STAFF and OUTSIDER are allowed.")
        return v


class ShopMemberUpdate(BaseModel):
    role: UserRole | None = None
    status: MembershipStatus | None = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: UserRole | None) -> UserRole | None:
        if v == UserRole.OWNER:
            raise ValueError("Cannot assign OWNER role to a member. Only STAFF and OUTSIDER are allowed.")
        return v


class ShopMemberResponse(ShopMemberBase):
    id: uuid.UUID
    shop_id: uuid.UUID
    user_id: uuid.UUID
    status: MembershipStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
