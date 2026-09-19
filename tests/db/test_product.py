"""Tests for Product — shop-scoped creation, deactivation, duplicate name constraint."""
import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from app.models.user import User
from app.models.shop import Shop
from app.models.product import Product
from app.models.statement import Statement
from app.models.enums import SpeakerStatus, StatementStatus, StatementSource


class TestProductModel:

    def _make_shop(self, db, owner_phone: str, shop_name: str = "Test Shop"):
        owner = User(name="Owner", phone=owner_phone)
        db.add(owner)
        db.flush()
        shop = Shop(name=shop_name, owner_id=owner.id)
        db.add(shop)
        db.flush()
        return owner, shop

    def test_product_creation(self, db):
        """A product can be created belonging to a shop."""
        _, shop = self._make_shop(db, "+919876542001")
        product = Product(shop_id=shop.id, name="Rice", default_unit="bag")
        db.add(product)
        db.commit()
        db.refresh(product)

        assert product.id is not None
        assert product.name == "Rice"
        assert product.default_unit == "bag"
        assert product.shop_id == shop.id
        assert product.is_active is True

    def test_products_are_shop_specific(self, db):
        """
        Two different shops can have products with the same name.
        They are separate entities — shop isolation is preserved.
        """
        _, shop_a = self._make_shop(db, "+919876542002", "Shop A")
        _, shop_b = self._make_shop(db, "+919876542003", "Shop B")

        rice_a = Product(shop_id=shop_a.id, name="Rice", default_unit="bag")
        rice_b = Product(shop_id=shop_b.id, name="Rice", default_unit="kg")
        db.add_all([rice_a, rice_b])
        db.commit()
        db.refresh(rice_a)
        db.refresh(rice_b)

        assert rice_a.shop_id == shop_a.id
        assert rice_b.shop_id == shop_b.id
        assert rice_a.id != rice_b.id
        # Different units confirms they are separate configurable entities
        assert rice_a.default_unit != rice_b.default_unit

    def test_duplicate_product_name_in_same_shop_rejected(self, db):
        """Same product name cannot exist twice in the same shop."""
        _, shop = self._make_shop(db, "+919876542004")
        p1 = Product(shop_id=shop.id, name="Sugar", default_unit="kg")
        db.add(p1)
        db.commit()

        p2 = Product(shop_id=shop.id, name="Sugar", default_unit="bag")
        db.add(p2)
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

    def test_product_deactivation_preserves_statements(self, db):
        """
        Deactivating a product does NOT delete historical statements.
        This verifies audit integrity (Contract §45.2, §45.4).
        """
        owner, shop = self._make_shop(db, "+919876542005")
        product = Product(shop_id=shop.id, name="Oil", default_unit="carton")
        db.add(product)
        db.flush()

        stmt = Statement(
            shop_id=shop.id,
            product_id=product.id,
            speaker_status=SpeakerStatus.IDENTIFIED,
            status=StatementStatus.CONFIRMED,
            source=StatementSource.MOBILE_WEB,
        )
        db.add(stmt)
        db.commit()

        # Deactivate product
        product.is_active = False
        db.commit()

        # Statement is still queryable — historical integrity preserved
        result = db.execute(
            select(Statement).where(Statement.id == stmt.id)
        ).scalar_one()
        assert result is not None
        assert result.product_id == product.id
        assert result.status == StatementStatus.CONFIRMED
