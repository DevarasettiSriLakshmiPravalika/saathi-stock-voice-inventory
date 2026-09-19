"""Tests for ShopMember — creation, roles, duplicate prevention."""
import pytest
from sqlalchemy.exc import IntegrityError
from app.models.user import User
from app.models.shop import Shop
from app.models.shop_member import ShopMember
from app.models.enums import UserRole, MembershipStatus


class TestShopMemberModel:

    def _setup(self, db, owner_phone: str, staff_phone: str):
        owner = User(name="Owner", phone=owner_phone)
        db.add(owner)
        db.flush()
        shop = Shop(name="Test Shop", owner_id=owner.id)
        db.add(shop)
        db.flush()
        staff = User(name="Staff Member", phone=staff_phone)
        db.add(staff)
        db.flush()
        return owner, shop, staff

    def test_membership_creation(self, db):
        """A staff member can be added to a shop."""
        owner, shop, staff = self._setup(db, "+919876541001", "+919876541002")
        member = ShopMember(shop_id=shop.id, user_id=staff.id, role=UserRole.STAFF)
        db.add(member)
        db.commit()
        db.refresh(member)

        assert member.id is not None
        assert member.role == UserRole.STAFF
        assert member.status == MembershipStatus.ACTIVE

    def test_outsider_membership(self, db):
        """An outsider can be added to a shop with OUTSIDER role."""
        owner, shop, outsider = self._setup(db, "+919876541003", "+919876541004")
        member = ShopMember(shop_id=shop.id, user_id=outsider.id, role=UserRole.OUTSIDER)
        db.add(member)
        db.commit()
        db.refresh(member)

        assert member.role == UserRole.OUTSIDER

    def test_owner_membership(self, db):
        """Owner can be recorded as OWNER-role member of the shop."""
        owner, shop, _ = self._setup(db, "+919876541005", "+919876541006")
        member = ShopMember(shop_id=shop.id, user_id=owner.id, role=UserRole.OWNER)
        db.add(member)
        db.commit()
        db.refresh(member)

        assert member.role == UserRole.OWNER

    def test_duplicate_membership_rejected(self, db):
        """Same user cannot be a member of the same shop twice (unique constraint)."""
        owner, shop, staff = self._setup(db, "+919876541007", "+919876541008")
        m1 = ShopMember(shop_id=shop.id, user_id=staff.id, role=UserRole.STAFF)
        db.add(m1)
        db.commit()

        m2 = ShopMember(shop_id=shop.id, user_id=staff.id, role=UserRole.OUTSIDER)
        db.add(m2)
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

    def test_membership_deactivation(self, db):
        """Member can be soft-deactivated (status=INACTIVE) without physical deletion."""
        owner, shop, staff = self._setup(db, "+919876541009", "+919876541010")
        member = ShopMember(shop_id=shop.id, user_id=staff.id, role=UserRole.STAFF)
        db.add(member)
        db.commit()

        member.status = MembershipStatus.INACTIVE
        db.commit()
        db.refresh(member)

        assert member.status == MembershipStatus.INACTIVE
        assert member.id is not None  # Record preserved

    def test_relationship_to_shop_and_user(self, db):
        """ShopMember relationships to Shop and User resolve correctly."""
        owner, shop, staff = self._setup(db, "+919876541011", "+919876541012")
        member = ShopMember(shop_id=shop.id, user_id=staff.id, role=UserRole.STAFF)
        db.add(member)
        db.commit()
        db.refresh(member)

        assert member.shop.id == shop.id
        assert member.user.id == staff.id
