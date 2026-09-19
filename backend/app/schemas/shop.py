import uuid
from datetime import datetime
from pydantic import BaseModel


class ShopBase(BaseModel):
    name: str


class ShopCreate(ShopBase):
    pass


class ShopUpdate(BaseModel):
    name: str | None = None
    is_active: bool | None = None


class ShopResponse(ShopBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
