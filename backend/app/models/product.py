import uuid
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Boolean, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.shop import Shop
    from app.models.baseline import Baseline
    from app.models.statement import Statement


class Product(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    A shop-specific product.

    Shop isolation: Shop A's "Rice" and Shop B's "Rice" are SEPARATE entities.
    Never create globally shared products — doing so would break shop isolation.

    Historical statements reference product_id and must remain auditable
    even after a product is deactivated (is_active=False).
    No physical deletion of products that have associated statements.

    CRITICAL: There is NO current_stock column here.
    Inventory is derived at query time:
        Latest Baseline + SUM(CONFIRMED IN) - SUM(CONFIRMED OUT)
    """
    __tablename__ = "products"
    __table_args__ = (
        # Two shops may have products with the same name — constraint is per-shop.
        UniqueConstraint("shop_id", "name", name="uq_products_shop_name"),
        Index("ix_products_shop_id", "shop_id"),
    )

    shop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shops.id", ondelete="RESTRICT"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    default_unit: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    shop: Mapped["Shop"] = relationship("Shop", back_populates="products")
    baselines: Mapped[List["Baseline"]] = relationship("Baseline", back_populates="product", lazy="select")
    statements: Mapped[List["Statement"]] = relationship("Statement", back_populates="product", lazy="select")
