import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel


class BaselineCreate(BaseModel):
    product_id: uuid.UUID
    quantity: Decimal
    unit: str
    notes: Optional[str] = None


class BaselineResponse(BaseModel):
    id: uuid.UUID
    shop_id: uuid.UUID
    product_id: uuid.UUID
    quantity: Decimal
    unit: str
    created_by_id: uuid.UUID
    is_superseded: bool
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
