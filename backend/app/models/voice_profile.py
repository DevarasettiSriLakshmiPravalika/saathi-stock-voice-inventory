import uuid
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, ForeignKey, Float, Text, Index
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin
from app.models.enums import VoiceEnrollmentStatus

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.shop import Shop


class VoiceProfile(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Speaker voice profile for a user within a specific shop context.

    Security / Privacy (Contract §48):
    - The `embedding` column contains biometric-adjacent speaker data.
    - It must NEVER be returned in normal API responses (excluded from schemas).
    - Voice profiles are shop-scoped: a user re-enrolls per shop if required.
    - Raw audio is NOT stored here; only the derived embedding vector.

    Embedding storage rationale:
    - Stored as JSONB (list of floats) inside PostgreSQL for Phase 1.
    - This avoids external storage dependencies at this stage.
    - The JSONB column is documented as sensitive and excluded from all
      public-facing Pydantic response schemas.
    - A future phase may migrate to a vector database or external store;
      the `embedding` column can then hold an external reference key instead.
    """
    __tablename__ = "voice_profiles"
    __table_args__ = (
        Index("ix_voice_profiles_user_id", "user_id"),
        Index("ix_voice_profiles_shop_id", "shop_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    # Shop context: enrollment is per shop (shop-isolated)
    shop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shops.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # ── Sensitive: NEVER expose via API ───────────────────────────────────────
    # Stored as JSONB list[float]. Excluded from all Pydantic response schemas.
    embedding: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    # ─────────────────────────────────────────────────────────────────────────

    enrollment_status: Mapped[VoiceEnrollmentStatus] = mapped_column(
        SAEnum(VoiceEnrollmentStatus, name="voice_enrollment_status", create_type=False),
        nullable=False,
        default=VoiceEnrollmentStatus.FAILED,
    )
    # Quality metadata for debugging / re-enrollment decisions
    quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    audio_duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    model_version: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="voice_profiles")
    shop: Mapped["Shop"] = relationship("Shop", foreign_keys=[shop_id])
