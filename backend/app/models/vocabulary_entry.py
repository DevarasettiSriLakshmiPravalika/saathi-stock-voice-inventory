import uuid
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean, ForeignKey, UniqueConstraint, Index, Numeric
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin
from app.models.enums import VocabularyMappingType

if TYPE_CHECKING:
    from app.models.shop import Shop
    from app.models.product import Product


class VocabularyEntry(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Shop-specific vocabulary mapping (Contract §24).

    Supports entity resolution — e.g., "chawal" → Rice product.

    CRITICAL isolation rule:
        Shop A vocabulary ≠ Shop B vocabulary.
    A mapping MUST NOT automatically propagate to other shops.

    Mapping types:
    - PRODUCT_ALIAS  → source_term maps to a specific product (target_product_id)
    - UNIT_ALIAS     → source_term maps to a canonical unit (target_unit)
    - UNIT_CONVERSION → source_term unit converts to target_unit via conversion_factor
    """
    __tablename__ = "vocabulary_entries"
    __table_args__ = (
        # One source_term+type combination per shop — no duplicates
        UniqueConstraint("shop_id", "source_term", "mapping_type", name="uq_vocabulary_shop_term_type"),
        Index("ix_vocabulary_shop_id", "shop_id"),
    )

    shop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shops.id", ondelete="RESTRICT"),
        nullable=False,
    )
    source_term: Mapped[str] = mapped_column(String(255), nullable=False)
    mapping_type: Mapped[VocabularyMappingType] = mapped_column(
        SAEnum(VocabularyMappingType, name="vocabulary_mapping_type", create_type=False),
        nullable=False,
    )
    # For PRODUCT_ALIAS
    target_product_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=True,
    )
    # For UNIT_ALIAS / UNIT_CONVERSION
    target_unit: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    # Conversion factor — the system must not invent this; it must be explicitly configured
    conversion_factor: Mapped[Optional[float]] = mapped_column(
        Numeric(precision=18, scale=6), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    shop: Mapped["Shop"] = relationship("Shop", back_populates="vocabulary_entries")
    target_product: Mapped[Optional["Product"]] = relationship(
        "Product", foreign_keys=[target_product_id]
    )
