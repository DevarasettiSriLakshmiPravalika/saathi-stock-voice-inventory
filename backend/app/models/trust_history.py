import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, ForeignKey, Numeric, Text, DateTime, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.models.base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.shop import Shop
    from app.models.user import User
    from app.models.statement import Statement
    from app.models.review import Review


class TrustHistory(Base, UUIDPrimaryKeyMixin):
    """
    Auditable history of speaker trust changes (Contract §26 / §37).

    Trust rules:
    - Trust is SHOP-SPECIFIC — one shop's assessment does not transfer.
    - Trust changes are APPEND-ONLY — never modify historical records.
    - Every change records the previous state, new state, trigger, and reason.
    - Owner actions (review approve/reject/override) may influence trust.

    occurred_at: when the trust-affecting event actually happened.
    created_at:  when this history record was inserted (may differ).

    metadata_ column (stored as "metadata" in DB): any additional context
    about the trust change. Do not store raw audio or biometric data here.
    """
    __tablename__ = "trust_history"
    __table_args__ = (
        Index("ix_trust_history_shop_id", "shop_id"),
        Index("ix_trust_history_user_id", "user_id"),
        Index("ix_trust_history_shop_user", "shop_id", "user_id"),
    )

    shop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shops.id", ondelete="RESTRICT"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    previous_trust_score: Mapped[Optional[float]] = mapped_column(
        Numeric(precision=5, scale=4), nullable=True  # null for first entry
    )
    new_trust_score: Mapped[float] = mapped_column(
        Numeric(precision=5, scale=4), nullable=False
    )
    trigger_event: Mapped[str] = mapped_column(String(100), nullable=False)
    related_statement_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("statements.id", ondelete="RESTRICT"),
        nullable=True,
    )
    related_review_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("reviews.id", ondelete="RESTRICT"),
        nullable=True,
    )
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # "metadata" is a reserved word in some contexts; mapped via column name alias
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB, nullable=True)

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    shop: Mapped["Shop"] = relationship("Shop", back_populates="trust_histories")
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    related_statement: Mapped[Optional["Statement"]] = relationship(
        "Statement", foreign_keys=[related_statement_id]
    )
    related_review: Mapped[Optional["Review"]] = relationship(
        "Review", foreign_keys=[related_review_id]
    )
