import uuid
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean, ForeignKey, Numeric, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.shop import Shop
    from app.models.product import Product
    from app.models.user import User


class Baseline(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Inventory baseline — a deliberate manual stock count by the owner.

    APPEND-ONLY design:
    - Historical baselines are NEVER overwritten or deleted.
    - When a new baseline is set, the previous one is marked is_superseded=True.
    - The inventory engine uses the LATEST non-superseded baseline per product.

    Inventory formula (Contract §34):
        Current Stock = Latest Baseline
                      + SUM of CONFIRMED IN statements after baseline date
                      - SUM of CONFIRMED OUT statements after baseline date

    This table stores the events that feed that formula — not a running total.
    """
    __tablename__ = "baselines"
    __table_args__ = (
        Index("ix_baselines_shop_id", "shop_id"),
        Index("ix_baselines_product_id", "product_id"),
        Index("ix_baselines_shop_product", "shop_id", "product_id"),
    )

    shop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shops.id", ondelete="RESTRICT"),
        nullable=False,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
    )
    quantity: Mapped[float] = mapped_column(Numeric(precision=18, scale=4), nullable=False)
    unit: Mapped[str] = mapped_column(String(100), nullable=False)
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    # Marks whether a newer baseline supersedes this one.
    # The most-recent non-superseded baseline is the active one.
    is_superseded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    shop: Mapped["Shop"] = relationship("Shop", back_populates="baselines")
    product: Mapped["Product"] = relationship("Product", back_populates="baselines")
    created_by: Mapped["User"] = relationship("User", foreign_keys=[created_by_id])
