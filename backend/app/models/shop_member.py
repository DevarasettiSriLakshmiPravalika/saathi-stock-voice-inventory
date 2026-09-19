import uuid
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, UniqueConstraint, Index
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin
from app.models.enums import UserRole, MembershipStatus

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.shop import Shop


class ShopMember(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Associates a User with a Shop under a specific Role.

    Contract rules enforced here:
    - A user may not be a member of the same shop twice (unique constraint).
    - Owner is assigned OWNER role; staff/outsiders are added by the owner.
    - Use status=INACTIVE instead of physical deletion to preserve audit trail.
    """
    __tablename__ = "shop_members"
    __table_args__ = (
        # Prevent duplicate membership for same user+shop regardless of role.
        UniqueConstraint("shop_id", "user_id", name="uq_shop_members_shop_user"),
        Index("ix_shop_members_shop_id", "shop_id"),
        Index("ix_shop_members_user_id", "user_id"),
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
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role", create_type=False),
        nullable=False,
    )
    status: Mapped[MembershipStatus] = mapped_column(
        SAEnum(MembershipStatus, name="membership_status", create_type=False),
        default=MembershipStatus.ACTIVE,
        nullable=False,
    )

    # Relationships
    shop: Mapped["Shop"] = relationship("Shop", back_populates="members")
    user: Mapped["User"] = relationship("User", back_populates="shop_memberships")
