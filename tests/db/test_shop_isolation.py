"""
Shop isolation tests.

Verifies that records belonging to Shop A are not accessible through
Shop B's relationship/query paths.

This is a critical security property (Contract §45.1, §22).
"""
import pytest
from sqlalchemy import select
from app.models.user import User
from app.models.shop import Shop
from app.models.product import Product
from app.models.statement import Statement
from app.models.vocabulary_entry import VocabularyEntry
from app.models.baseline import Baseline
from app.models.trust_history import TrustHistory
from app.models.enums import (
    SpeakerStatus,
    StatementStatus,
    StatementSource,
    VocabularyMappingType,
)


class TestShopIsolation:

    def _make_shop(self, db, phone: str, shop_name: str):
        owner = User(name="Owner", phone=phone)
        db.add(owner)
        db.flush()
        shop = Shop(name=shop_name, owner_id=owner.id)
        db.add(shop)
        db.flush()
        return owner, shop

    def test_product_isolation(self, db):
        """
        Querying Shop A products returns ONLY Shop A products.
        Shop B products are not in the result.
        """
        _, shop_a = self._make_shop(db, "+919876544001", "Shop A")
        _, shop_b = self._make_shop(db, "+919876544002", "Shop B")

        prod_a = Product(shop_id=shop_a.id, name="Rice", default_unit="bag")
        prod_b = Product(shop_id=shop_b.id, name="Sugar", default_unit="kg")
        db.add_all([prod_a, prod_b])
        db.commit()

        shop_a_products = db.execute(
            select(Product).where(Product.shop_id == shop_a.id)
        ).scalars().all()

        assert all(p.shop_id == shop_a.id for p in shop_a_products)
        product_ids = [p.id for p in shop_a_products]
        assert prod_b.id not in product_ids

    def test_statement_isolation(self, db):
        """
        Querying Shop A statements returns ONLY Shop A statements.
        """
        _, shop_a = self._make_shop(db, "+919876544003", "Shop A2")
        _, shop_b = self._make_shop(db, "+919876544004", "Shop B2")

        stmt_a = Statement(
            shop_id=shop_a.id,
            speaker_status=SpeakerStatus.IDENTIFIED,
            status=StatementStatus.CONFIRMED,
            source=StatementSource.MOBILE_WEB,
        )
        stmt_b = Statement(
            shop_id=shop_b.id,
            speaker_status=SpeakerStatus.IDENTIFIED,
            status=StatementStatus.CONFIRMED,
            source=StatementSource.MOBILE_WEB,
        )
        db.add_all([stmt_a, stmt_b])
        db.commit()

        shop_a_stmts = db.execute(
            select(Statement).where(Statement.shop_id == shop_a.id)
        ).scalars().all()

        assert all(s.shop_id == shop_a.id for s in shop_a_stmts)
        stmt_ids = [s.id for s in shop_a_stmts]
        assert stmt_b.id not in stmt_ids

    def test_vocabulary_isolation(self, db):
        """
        Shop A vocabulary is not returned when querying Shop B.
        Contract §24: vocabulary MUST NOT propagate between shops.
        """
        _, shop_a = self._make_shop(db, "+919876544005", "Shop A3")
        _, shop_b = self._make_shop(db, "+919876544006", "Shop B3")

        prod_a = Product(shop_id=shop_a.id, name="Rice", default_unit="bag")
        db.add(prod_a)
        db.flush()

        vocab_a = VocabularyEntry(
            shop_id=shop_a.id,
            source_term="chawal",
            mapping_type=VocabularyMappingType.PRODUCT_ALIAS,
            target_product_id=prod_a.id,
        )
        db.add(vocab_a)
        db.commit()

        shop_b_vocab = db.execute(
            select(VocabularyEntry).where(VocabularyEntry.shop_id == shop_b.id)
        ).scalars().all()

        assert len(shop_b_vocab) == 0, (
            "Shop B must not inherit Shop A vocabulary. "
            "Vocabulary must be shop-isolated."
        )

    def test_trust_history_isolation(self, db):
        """Trust history for Shop A user is not accessible from Shop B's path."""
        owner_a, shop_a = self._make_shop(db, "+919876544007", "Shop A4")
        _, shop_b = self._make_shop(db, "+919876544008", "Shop B4")

        trust = TrustHistory(
            shop_id=shop_a.id,
            user_id=owner_a.id,
            new_trust_score=0.8,
            trigger_event="INITIAL",
        )
        db.add(trust)
        db.commit()

        shop_b_trust = db.execute(
            select(TrustHistory).where(TrustHistory.shop_id == shop_b.id)
        ).scalars().all()

        assert len(shop_b_trust) == 0, (
            "Shop B must not have access to Shop A trust history. "
            "Trust is shop-specific (Contract §26)."
        )

    def test_baseline_isolation(self, db):
        """Baselines for Shop A are not returned in Shop B queries."""
        owner_a, shop_a = self._make_shop(db, "+919876544009", "Shop A5")
        _, shop_b = self._make_shop(db, "+919876544010", "Shop B5")

        product_a = Product(shop_id=shop_a.id, name="Dal", default_unit="kg")
        db.add(product_a)
        db.flush()

        baseline = Baseline(
            shop_id=shop_a.id,
            product_id=product_a.id,
            quantity=50.0,
            unit="kg",
            created_by_id=owner_a.id,
        )
        db.add(baseline)
        db.commit()

        shop_b_baselines = db.execute(
            select(Baseline).where(Baseline.shop_id == shop_b.id)
        ).scalars().all()

        assert len(shop_b_baselines) == 0
