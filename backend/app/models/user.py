import uuid
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Boolean, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.shop_member import ShopMember
    from app.models.voice_profile import VoiceProfile


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Represents a Saathi user (owner, staff, or outsider).

    Security notes:
    - No passwords or OTP secrets stored here.
    - Authentication tokens are managed separately.
    - Deactivation (is_active=False) preferred over physical deletion
      to preserve audit integrity.
    """
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("phone", name="uq_users_phone"),
        Index("ix_users_phone", "phone"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Phone must be unique and normalised (E.164 recommended).
    phone: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_phone_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    shop_memberships: Mapped[List["ShopMember"]] = relationship(
        "ShopMember", back_populates="user", lazy="select"
    )
    voice_profiles: Mapped[List["VoiceProfile"]] = relationship(
        "VoiceProfile", back_populates="user", lazy="select"
    )
