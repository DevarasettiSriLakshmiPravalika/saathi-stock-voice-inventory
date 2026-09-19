import uuid
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Boolean, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.shop_member import ShopMember
    from app.models.product import Product
    from app.models.baseline import Baseline
    from app.models.vocabulary_entry import VocabularyEntry
    from app.models.statement import Statement
    from app.models.review import Review
    from app.models.trust_history import TrustHistory
    from app.models.audit_log import AuditLog


class Shop(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    A Saathi shop — the primary unit of shop isolation.

    Every shop-owned domain record (products, statements, vocabulary, etc.)
    is associated with exactly one shop.  The backend must enforce that
    users from Shop A cannot access Shop B data.

    A shop has exactly one logical owner (owner_id FK).  Ownership is
    additionally recorded in ShopMember with role=OWNER.
    """
    __tablename__ = "shops"
    __table_args__ = (
        Index("ix_shops_owner_id", "owner_id"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    owner: Mapped["User"] = relationship("User", foreign_keys=[owner_id], lazy="select")
    members: Mapped[List["ShopMember"]] = relationship("ShopMember", back_populates="shop", lazy="select")
    products: Mapped[List["Product"]] = relationship("Product", back_populates="shop", lazy="select")
    baselines: Mapped[List["Baseline"]] = relationship("Baseline", back_populates="shop", lazy="select")
    vocabulary_entries: Mapped[List["VocabularyEntry"]] = relationship("VocabularyEntry", back_populates="shop", lazy="select")
    statements: Mapped[List["Statement"]] = relationship("Statement", back_populates="shop", lazy="select")
    reviews: Mapped[List["Review"]] = relationship("Review", back_populates="shop", lazy="select")
    trust_histories: Mapped[List["TrustHistory"]] = relationship("TrustHistory", back_populates="shop", lazy="select")
    audit_logs: Mapped[List["AuditLog"]] = relationship("AuditLog", back_populates="shop", lazy="select")
