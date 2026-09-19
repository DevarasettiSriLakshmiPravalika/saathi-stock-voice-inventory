import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.enums import ReviewStatus, ReviewDecision


class ReviewResponse(BaseModel):
    id: uuid.UUID
    statement_id: uuid.UUID
    shop_id: uuid.UUID
    reviewer_id: Optional[uuid.UUID]
    status: ReviewStatus
    decision: Optional[ReviewDecision]
    reason: Optional[str]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReviewActionRequest(BaseModel):
    """Owner provides an optional reason when approving/rejecting/overriding."""
    reason: Optional[str] = None
