import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import ForeignKey, Text, DateTime, Index
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin
from app.models.enums import ReviewStatus, ReviewDecision

if TYPE_CHECKING:
    from app.models.statement import Statement
    from app.models.shop import Shop
    from app.models.user import User


class Review(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Owner review of a flagged statement (Contract §6 / §35).

    Every owner decision is permanently recorded — the original statement
    decision is NEVER erased.

    Owner actions:
    - APPROVED  → statement transitions to CONFIRMED, affects inventory
    - REJECTED  → statement remains REJECTED, no inventory effect
    - OVERRIDDEN → owner provides corrected values; both original and
                   override are preserved in Statement + AuditLog

    reviewer_id is nullable until the review is completed.
    completed_at is set when status → COMPLETED.
    """
    __tablename__ = "reviews"
    __table_args__ = (
        Index("ix_reviews_shop_id", "shop_id"),
        Index("ix_reviews_statement_id", "statement_id"),
        Index("ix_reviews_status", "status"),
        Index("ix_reviews_shop_status", "shop_id", "status"),
    )

    statement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("statements.id", ondelete="RESTRICT"),
        nullable=False,
    )
    shop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shops.id", ondelete="RESTRICT"),
        nullable=False,
    )
    # Nullable until review is completed
    reviewer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )
    status: Mapped[ReviewStatus] = mapped_column(
        SAEnum(ReviewStatus, name="review_status", create_type=False),
        nullable=False,
        default=ReviewStatus.PENDING,
    )
    decision: Mapped[Optional[ReviewDecision]] = mapped_column(
        SAEnum(ReviewDecision, name="review_decision", create_type=False),
        nullable=True,
    )
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    statement: Mapped["Statement"] = relationship("Statement", back_populates="reviews")
    shop: Mapped["Shop"] = relationship("Shop", back_populates="reviews")
    reviewer: Mapped[Optional["User"]] = relationship("User", foreign_keys=[reviewer_id])
