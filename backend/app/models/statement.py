import uuid
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Boolean, ForeignKey, Numeric, Text, DateTime, Index
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin
from app.models.enums import (
    StatementStatus,
    DecisionEnum,
    DirectionEnum,
    SpeakerStatus,
    StatementSource,
)

if TYPE_CHECKING:
    from app.models.shop import Shop
    from app.models.user import User
    from app.models.product import Product
    from app.models.voice_profile import VoiceProfile
    from app.models.statement_processing import StatementProcessing
    from app.models.review import Review


class Statement(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    The core ledger record — APPEND-ONLY (Contract §30).

    Statements are NEVER rewritten or deleted after creation.
    Corrections happen ONLY through:
        Review → ReviewDecision (APPROVED / REJECTED / OVERRIDDEN)
        AuditLog entries

    Inventory is derived from CONFIRMED statements only:
        Current Stock = Latest Baseline
                      + SUM(CONFIRMED, direction=IN, after baseline)
                      - SUM(CONFIRMED, direction=OUT, after baseline)

    Only the deterministic decision engine may set status=CONFIRMED.
    The LLM must never directly affect inventory (Contract §1.4).

    Override tracking:
    - is_overridden / override_by_id / override_reason / override_at
      are additive fields that RECORD an override without erasing the
      original decision or transcript.
    """
    __tablename__ = "statements"
    __table_args__ = (
        Index("ix_statements_shop_id", "shop_id"),
        Index("ix_statements_product_id", "product_id"),
        Index("ix_statements_actor_id", "actor_id"),
        Index("ix_statements_status", "status"),
        Index("ix_statements_decision", "decision"),
        Index("ix_statements_created_at", "created_at"),
        # Composite indexes for common query patterns
        Index("ix_statements_shop_status", "shop_id", "status"),
        Index("ix_statements_shop_created", "shop_id", "created_at"),
    )

    # ── Core identification ────────────────────────────────────────────────────
    shop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shops.id", ondelete="RESTRICT"),
        nullable=False,
    )
    # actor_id is nullable — speaker may be UNKNOWN
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )
    voice_profile_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("voice_profiles.id", ondelete="RESTRICT"),
        nullable=True,
    )
    product_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=True,
    )

    # ── Speaker state ──────────────────────────────────────────────────────────
    speaker_status: Mapped[SpeakerStatus] = mapped_column(
        SAEnum(SpeakerStatus, name="speaker_status", create_type=False),
        nullable=False,
    )
    speaker_confidence: Mapped[Optional[float]] = mapped_column(
        Numeric(precision=5, scale=4), nullable=True
    )

    # ── Original transcript (preserved for audit) ──────────────────────────────
    transcript: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Structured claim produced by LLM (read-only after creation) ───────────
    raw_claim: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # ── Resolved inventory fields ──────────────────────────────────────────────
    quantity: Mapped[Optional[float]] = mapped_column(
        Numeric(precision=18, scale=4), nullable=True
    )
    unit: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    direction: Mapped[Optional[DirectionEnum]] = mapped_column(
        SAEnum(DirectionEnum, name="direction_enum", create_type=False),
        nullable=True,
    )

    # ── Decision and pipeline status ───────────────────────────────────────────
    status: Mapped[StatementStatus] = mapped_column(
        SAEnum(StatementStatus, name="statement_status", create_type=False),
        nullable=False,
        default=StatementStatus.PENDING,
    )
    decision: Mapped[Optional[DecisionEnum]] = mapped_column(
        SAEnum(DecisionEnum, name="decision_enum", create_type=False),
        nullable=True,
    )

    # ── Source / channel ───────────────────────────────────────────────────────
    source: Mapped[StatementSource] = mapped_column(
        SAEnum(StatementSource, name="statement_source", create_type=False),
        nullable=False,
        default=StatementSource.MOBILE_WEB,
    )

    # ── Override tracking (additive — original is preserved) ──────────────────
    is_overridden: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    override_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )
    override_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    override_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Event time (when the inventory event actually occurred) ────────────────
    # Distinct from created_at (when the record was inserted)
    event_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    shop: Mapped["Shop"] = relationship("Shop", back_populates="statements")
    actor: Mapped[Optional["User"]] = relationship("User", foreign_keys=[actor_id])
    override_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[override_by_id])
    voice_profile: Mapped[Optional["VoiceProfile"]] = relationship(
        "VoiceProfile", foreign_keys=[voice_profile_id]
    )
    product: Mapped[Optional["Product"]] = relationship("Product", back_populates="statements")
    processing: Mapped[Optional["StatementProcessing"]] = relationship(
        "StatementProcessing", back_populates="statement", uselist=False
    )
    reviews: Mapped[List["Review"]] = relationship("Review", back_populates="statement")
