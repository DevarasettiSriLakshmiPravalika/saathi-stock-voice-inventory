import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.enums import VoiceEnrollmentStatus


class VoiceProfileResponse(BaseModel):
    """
    Public-facing voice profile schema.

    CRITICAL: The `embedding` field is intentionally EXCLUDED.
    Voice embeddings are biometric-adjacent data and must NEVER
    be returned through normal API responses (Contract §48).
    """
    id: uuid.UUID
    user_id: uuid.UUID
    shop_id: uuid.UUID
    enrollment_status: VoiceEnrollmentStatus
    quality_score: Optional[float]
    audio_duration_seconds: Optional[float]
    model_version: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
    # embedding is intentionally omitted — it is sensitive biometric data
