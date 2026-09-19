import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, Any
from pydantic import BaseModel
from app.models.enums import (
    StatementStatus,
    DecisionEnum,
    DirectionEnum,
    SpeakerStatus,
    StatementSource,
)


class StatementResponse(BaseModel):
    """
    Public-facing statement schema.

    raw_claim is included (LLM output) but is read-only after creation.
    Original transcript is preserved for auditability.
    Override fields are additive — original decision is never erased.
    """
    id: uuid.UUID
    shop_id: uuid.UUID
    actor_id: Optional[uuid.UUID]
    product_id: Optional[uuid.UUID]
    speaker_status: SpeakerStatus
    speaker_confidence: Optional[float]
    transcript: Optional[str]
    raw_claim: Optional[Any]
    quantity: Optional[Decimal]
    unit: Optional[str]
    direction: Optional[DirectionEnum]
    status: StatementStatus
    decision: Optional[DecisionEnum]
    source: StatementSource
    is_overridden: bool
    override_reason: Optional[str]
    override_at: Optional[datetime]
    event_time: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class StatementFilterParams(BaseModel):
    """Query parameters for filtering statements."""
    product_id: Optional[uuid.UUID] = None
    actor_id: Optional[uuid.UUID] = None
    status: Optional[StatementStatus] = None
    decision: Optional[DecisionEnum] = None
    direction: Optional[DirectionEnum] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
