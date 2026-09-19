import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, ForeignKey, Text, DateTime, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.models.base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.shop import Shop
    from app.models.user import User


class AuditLog(Base, UUIDPrimaryKeyMixin):
    """
    Immutable audit trail for all important system actions (Contract §20).

    Design choices:
    - action is stored as String (not enum) for extensibility across phases.
    - AuditAction enum in enums.py defines the canonical set of values;
      service code should always use those constants.
    - entity_type / entity_id give a generic FK-free reference to the
      affected record (avoids complex FK graph for audit purposes).
    - metadata_ (stored as "metadata") holds any additional context as JSONB.

    Security:
    - Do NOT log secrets, access tokens, or raw audio data.
    - Do NOT log voice embeddings or sensitive biometric information.

    shop_id is nullable: some actions (e.g. user registration) may occur
    before a shop is associated with the actor.
    """
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_shop_id", "shop_id"),
        Index("ix_audit_logs_actor_id", "actor_id"),
        Index("ix_audit_logs_created_at", "created_at"),
        Index("ix_audit_logs_shop_created", "shop_id", "created_at"),
    )

    # Nullable: pre-shop actions (registration) have no shop yet
    shop_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shops.id", ondelete="RESTRICT"),
        nullable=True,
    )
    # Nullable: system-generated events may have no actor
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )
    # String for extensibility; use AuditAction enum constants in application code
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    # Additional context — do NOT store secrets or sensitive audio data here
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    shop: Mapped[Optional["Shop"]] = relationship("Shop", back_populates="audit_logs")
    actor: Mapped[Optional["User"]] = relationship("User", foreign_keys=[actor_id])
