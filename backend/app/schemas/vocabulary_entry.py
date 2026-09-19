import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel
from app.models.enums import VocabularyMappingType


class VocabularyEntryBase(BaseModel):
    source_term: str
    mapping_type: VocabularyMappingType
    target_product_id: Optional[uuid.UUID] = None
    target_unit: Optional[str] = None
    conversion_factor: Optional[Decimal] = None


class VocabularyEntryCreate(VocabularyEntryBase):
    pass


class VocabularyEntryUpdate(BaseModel):
    target_product_id: Optional[uuid.UUID] = None
    target_unit: Optional[str] = None
    conversion_factor: Optional[Decimal] = None
    is_active: Optional[bool] = None


class VocabularyEntryResponse(VocabularyEntryBase):
    id: uuid.UUID
    shop_id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
