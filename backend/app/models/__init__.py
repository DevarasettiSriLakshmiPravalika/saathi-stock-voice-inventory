# Re-export all models so that:
# 1. Alembic can detect all tables via Base.metadata
# 2. Application code has a single import point
from app.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin
from app.models.enums import (
    UserRole,
    MembershipStatus,
    StatementStatus,
    DecisionEnum,
    DirectionEnum,
    SpeakerStatus,
    StatementSource,
    VoiceEnrollmentStatus,
    VocabularyMappingType,
    ReviewStatus,
    ReviewDecision,
    AuditAction,
)
from app.models.user import User
from app.models.shop import Shop
from app.models.shop_member import ShopMember
from app.models.product import Product
from app.models.baseline import Baseline
from app.models.voice_profile import VoiceProfile
from app.models.vocabulary_entry import VocabularyEntry
from app.models.statement import Statement
from app.models.statement_processing import StatementProcessing
from app.models.review import Review
from app.models.trust_history import TrustHistory
from app.models.audit_log import AuditLog

__all__ = [
    # Base
    "Base",
    "UUIDPrimaryKeyMixin",
    "TimestampMixin",
    # Enums
    "UserRole",
    "MembershipStatus",
    "StatementStatus",
    "DecisionEnum",
    "DirectionEnum",
    "SpeakerStatus",
    "StatementSource",
    "VoiceEnrollmentStatus",
    "VocabularyMappingType",
    "ReviewStatus",
    "ReviewDecision",
    "AuditAction",
    # Models
    "User",
    "Shop",
    "ShopMember",
    "Product",
    "Baseline",
    "VoiceProfile",
    "VocabularyEntry",
    "Statement",
    "StatementProcessing",
    "Review",
    "TrustHistory",
    "AuditLog",
]
