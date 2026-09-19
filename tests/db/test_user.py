"""Tests for the User model — creation, uniqueness constraints."""
import pytest
from sqlalchemy.exc import IntegrityError
from app.models.user import User


class TestUserModel:

    def test_user_creation(self, db):
        """User can be created with valid name and phone."""
        user = User(name="Test Owner", phone="+919876543210")
        db.add(user)
        db.commit()
        db.refresh(user)

        assert user.id is not None
        assert user.name == "Test Owner"
        assert user.phone == "+919876543210"
        assert user.is_active is True
        assert user.is_phone_verified is False
        assert user.created_at is not None
        assert user.updated_at is not None

    def test_unique_phone_constraint(self, db):
        """Two users cannot share the same phone number."""
        user1 = User(name="User One", phone="+919876543211")
        db.add(user1)
        db.commit()

        user2 = User(name="User Two", phone="+919876543211")
        db.add(user2)
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

    def test_user_deactivation(self, db):
        """User can be soft-deactivated (is_active=False) without physical deletion."""
        user = User(name="Inactive User", phone="+919876543212")
        db.add(user)
        db.commit()

        user.is_active = False
        db.commit()
        db.refresh(user)

        assert user.is_active is False
        assert user.id is not None  # Record still exists

    def test_phone_verification_flag(self, db):
        """is_phone_verified defaults to False and can be set to True."""
        user = User(name="Verified User", phone="+919876543213")
        db.add(user)
        db.commit()
        assert user.is_phone_verified is False

        user.is_phone_verified = True
        db.commit()
        db.refresh(user)
        assert user.is_phone_verified is True
