"""Tests for the Shop model — creation, owner relationship."""
import pytest
from app.models.user import User
from app.models.shop import Shop


class TestShopModel:

    def _make_owner(self, db, phone: str) -> User:
        owner = User(name="Shop Owner", phone=phone)
        db.add(owner)
        db.flush()
        return owner

    def test_shop_creation(self, db):
        """A shop can be created with a name and an owner."""
        owner = self._make_owner(db, "+919876540001")
        shop = Shop(name="My Test Shop", owner_id=owner.id)
        db.add(shop)
        db.commit()
        db.refresh(shop)

        assert shop.id is not None
        assert shop.name == "My Test Shop"
        assert shop.owner_id == owner.id
        assert shop.is_active is True
        assert shop.created_at is not None

    def test_shop_owner_relationship(self, db):
        """Shop.owner lazy-loads the correct User record."""
        owner = self._make_owner(db, "+919876540002")
        shop = Shop(name="Owner Relationship Shop", owner_id=owner.id)
        db.add(shop)
        db.commit()
        db.refresh(shop)

        assert shop.owner is not None
        assert shop.owner.id == owner.id
        assert shop.owner.name == "Shop Owner"

    def test_shop_requires_owner(self, db):
        """Shop cannot be created without a valid owner_id."""
        import uuid
        shop = Shop(name="Orphan Shop", owner_id=uuid.uuid4())
        db.add(shop)
        from sqlalchemy.exc import IntegrityError
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

    def test_shop_soft_deactivation(self, db):
        """Shop can be deactivated (is_active=False); record persists."""
        owner = self._make_owner(db, "+919876540003")
        shop = Shop(name="Deactivated Shop", owner_id=owner.id)
        db.add(shop)
        db.commit()

        shop.is_active = False
        db.commit()
        db.refresh(shop)

        assert shop.is_active is False
        assert shop.id is not None
