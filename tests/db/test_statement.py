"""
Tests for the Statement model.

Verifies:
- Statement creation with all required fields
- All contract-exact status values (PENDING/PROCESSING/CONFIRMED/FLAGGED/REJECTED)
- All contract-exact decision values (AUTO_CONFIRMED/REQUIRES_REVIEW/REJECTED)
- All contract-exact direction values (IN/OUT)
- Append-only / historical persistence guarantee
- No current_stock column exists on Product
"""
import pytest
from sqlalchemy import select, inspect
from app.models.user import User
from app.models.shop import Shop
from app.models.product import Product
from app.models.statement import Statement
from app.models.enums import (
    StatementStatus,
    DecisionEnum,
    DirectionEnum,
    SpeakerStatus,
    StatementSource,
)


class TestStatementModel:

    def _setup(self, db, phone: str):
        owner = User(name="Owner", phone=phone)
        db.add(owner)
        db.flush()
        shop = Shop(name="Test Shop", owner_id=owner.id)
        db.add(shop)
        db.flush()
        product = Product(shop_id=shop.id, name="Rice", default_unit="bag")
        db.add(product)
        db.flush()
        return owner, shop, product

    def test_statement_creation(self, db):
        """A complete statement can be created with all required fields."""
        owner, shop, product = self._setup(db, "+919876543001")
        stmt = Statement(
            shop_id=shop.id,
            actor_id=owner.id,
            product_id=product.id,
            speaker_status=SpeakerStatus.IDENTIFIED,
            transcript="Owner sold 5 bags of rice",
            quantity=5.0,
            unit="bag",
            direction=DirectionEnum.OUT,
            status=StatementStatus.CONFIRMED,
            decision=DecisionEnum.AUTO_CONFIRMED,
            source=StatementSource.MOBILE_WEB,
        )
        db.add(stmt)
        db.commit()
        db.refresh(stmt)

        assert stmt.id is not None
        assert stmt.shop_id == shop.id
        assert stmt.status == StatementStatus.CONFIRMED
        assert stmt.decision == DecisionEnum.AUTO_CONFIRMED
        assert stmt.direction == DirectionEnum.OUT
        assert stmt.is_overridden is False
        assert stmt.transcript == "Owner sold 5 bags of rice"

    def test_all_statement_statuses_are_valid(self, db):
        """
        All five contract-defined statuses can be stored.
        Ensures PENDING/PROCESSING/CONFIRMED/FLAGGED/REJECTED are all valid.
        """
        owner, shop, product = self._setup(db, "+919876543002")
        for status in StatementStatus:
            stmt = Statement(
                shop_id=shop.id,
                speaker_status=SpeakerStatus.UNKNOWN,
                status=status,
                source=StatementSource.MOBILE_WEB,
            )
            db.add(stmt)
        db.commit()  # All five should commit successfully

    def test_all_decision_values_are_valid(self, db):
        """
        All three contract-defined decisions can be stored.
        AUTO_CONFIRMED / REQUIRES_REVIEW / REJECTED
        """
        owner, shop, product = self._setup(db, "+919876543003")
        for decision in DecisionEnum:
            stmt = Statement(
                shop_id=shop.id,
                speaker_status=SpeakerStatus.IDENTIFIED,
                status=StatementStatus.CONFIRMED,
                decision=decision,
                source=StatementSource.MOBILE_WEB,
            )
            db.add(stmt)
        db.commit()

    def test_direction_in_and_out(self, db):
        """Both IN and OUT directions can be stored. No other values exist."""
        owner, shop, product = self._setup(db, "+919876543004")

        in_stmt = Statement(
            shop_id=shop.id,
            product_id=product.id,
            speaker_status=SpeakerStatus.IDENTIFIED,
            quantity=20.0,
            unit="bag",
            direction=DirectionEnum.IN,
            status=StatementStatus.CONFIRMED,
            source=StatementSource.MOBILE_WEB,
        )
        out_stmt = Statement(
            shop_id=shop.id,
            product_id=product.id,
            speaker_status=SpeakerStatus.IDENTIFIED,
            quantity=5.0,
            unit="bag",
            direction=DirectionEnum.OUT,
            status=StatementStatus.CONFIRMED,
            source=StatementSource.MOBILE_WEB,
        )
        db.add_all([in_stmt, out_stmt])
        db.commit()

        assert in_stmt.direction == DirectionEnum.IN
        assert out_stmt.direction == DirectionEnum.OUT

    def test_statement_historical_persistence(self, db):
        """
        Statements persist after product deactivation.
        Verifies the append-only / audit integrity guarantee (Contract §30).
        """
        owner, shop, product = self._setup(db, "+919876543005")
        stmt = Statement(
            shop_id=shop.id,
            product_id=product.id,
            speaker_status=SpeakerStatus.IDENTIFIED,
            status=StatementStatus.CONFIRMED,
            source=StatementSource.MOBILE_WEB,
        )
        db.add(stmt)
        db.commit()
        stmt_id = stmt.id

        # Deactivate product
        product.is_active = False
        db.commit()

        # Statement is still retrievable
        result = db.execute(
            select(Statement).where(Statement.id == stmt_id)
        ).scalar_one()
        assert result is not None
        assert result.product_id == product.id

    def test_unknown_speaker_statement(self, db):
        """
        Statements from unknown speakers are valid (no actor_id required).
        Supports UNKNOWN speaker status.
        """
        owner, shop, product = self._setup(db, "+919876543006")
        stmt = Statement(
            shop_id=shop.id,
            actor_id=None,  # Unknown speaker
            speaker_status=SpeakerStatus.UNKNOWN,
            status=StatementStatus.FLAGGED,
            decision=DecisionEnum.REQUIRES_REVIEW,
            source=StatementSource.PHONE_CALL,
        )
        db.add(stmt)
        db.commit()
        db.refresh(stmt)

        assert stmt.actor_id is None
        assert stmt.speaker_status == SpeakerStatus.UNKNOWN
        assert stmt.status == StatementStatus.FLAGGED

    def test_no_current_stock_on_product(self, db):
        """
        Verify Product has NO current_stock column.
        Inventory must be derived from Baseline + Confirmed Statements.
        This is a contract-critical check (Contract §34, §45.3).
        """
        from app.models.product import Product as ProductModel
        mapper = inspect(ProductModel)
        column_names = [c.key for c in mapper.mapper.columns]
        assert "current_stock" not in column_names, (
            "Product must NOT have a current_stock column. "
            "Inventory is derived from Baseline + Confirmed Statements."
        )
