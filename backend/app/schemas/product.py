import uuid
from datetime import datetime
from pydantic import BaseModel


class ProductBase(BaseModel):
    name: str
    default_unit: str


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: str | None = None
    default_unit: str | None = None
    is_active: bool | None = None


class ProductResponse(ProductBase):
    id: uuid.UUID
    shop_id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
