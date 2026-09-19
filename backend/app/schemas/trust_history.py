import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, Any
from pydantic import BaseModel


class TrustHistoryResponse(BaseModel):
    id: uuid.UUID
    shop_id: uuid.UUID
    user_id: uuid.UUID
    previous_trust_score: Optional[Decimal]
    new_trust_score: Decimal
    trigger_event: str
    related_statement_id: Optional[uuid.UUID]
    related_review_id: Optional[uuid.UUID]
    reason: Optional[str]
    occurred_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}
