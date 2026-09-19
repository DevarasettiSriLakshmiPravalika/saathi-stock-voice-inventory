"""
Saathi Enums — locked to the SAATHI_CONTRACT.md v1.0.0 definitions.

Do NOT introduce alternate values for any enum without first updating
the contract document and incrementing its version.
"""
import enum


# ─── User / Membership ────────────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    """
    Roles as defined in Contract §8 and §46.
    Allowed: OWNER | STAFF | OUTSIDER
    """
    OWNER = "OWNER"
    STAFF = "STAFF"
    OUTSIDER = "OUTSIDER"


class MembershipStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


# ─── Statement ────────────────────────────────────────────────────────────────

class StatementStatus(str, enum.Enum):
    """
    Contract §32 / §46. Exact values — do not add APPROVED, FAILED, REVIEW.
    """
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    CONFIRMED = "CONFIRMED"
    FLAGGED = "FLAGGED"
    REJECTED = "REJECTED"


class DecisionEnum(str, enum.Enum):
    """
    Contract §29 / §46.
    Decision and StatementStatus are RELATED but DISTINCT fields.
    """
    AUTO_CONFIRMED = "AUTO_CONFIRMED"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"
    REJECTED = "REJECTED"


class DirectionEnum(str, enum.Enum):
    """
    Contract §46. Only IN / OUT are valid.
    Do not use SALE, PURCHASE, ADD, REMOVE.
    """
    IN = "IN"
    OUT = "OUT"


class SpeakerStatus(str, enum.Enum):
    """
    Contract §21 / §46.
    Identity must not be assumed from LLM name inference alone.
    """
    IDENTIFIED = "IDENTIFIED"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    UNKNOWN = "UNKNOWN"


class StatementSource(str, enum.Enum):
    """Input channel through which the statement arrived."""
    MOBILE_WEB = "MOBILE_WEB"
    LIVE_MIC = "LIVE_MIC"
    PHONE_CALL = "PHONE_CALL"
    MANUAL = "MANUAL"


# ─── Voice ────────────────────────────────────────────────────────────────────

class VoiceEnrollmentStatus(str, enum.Enum):
    """
    Contract §18 / §46. Allowed enrollment outcomes.
    """
    ENROLLED = "ENROLLED"
    LOW_QUALITY = "LOW_QUALITY"
    FAILED = "FAILED"


# ─── Vocabulary ───────────────────────────────────────────────────────────────

class VocabularyMappingType(str, enum.Enum):
    """Contract §24. Shop-specific vocabulary mapping types."""
    PRODUCT_ALIAS = "PRODUCT_ALIAS"
    UNIT_ALIAS = "UNIT_ALIAS"
    UNIT_CONVERSION = "UNIT_CONVERSION"


# ─── Review ───────────────────────────────────────────────────────────────────

class ReviewStatus(str, enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"


class ReviewDecision(str, enum.Enum):
    """
    Contract §6 / §35. Owner actions: Approve | Reject | Override.
    Every decision is permanently recorded — original is never erased.
    """
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    OVERRIDDEN = "OVERRIDDEN"


# ─── Audit ────────────────────────────────────────────────────────────────────

class AuditAction(str, enum.Enum):
    """
    Contract §20 audit actions. Stored as string in AuditLog for extensibility.
    """
    OWNER_CREATED_SHOP = "OWNER_CREATED_SHOP"
    PRODUCT_CREATED = "PRODUCT_CREATED"
    PRODUCT_UPDATED = "PRODUCT_UPDATED"
    MEMBER_ADDED = "MEMBER_ADDED"
    MEMBER_UPDATED = "MEMBER_UPDATED"
    BASELINE_CREATED = "BASELINE_CREATED"
    VOICE_ENROLLED = "VOICE_ENROLLED"
    STATEMENT_CREATED = "STATEMENT_CREATED"
    STATEMENT_CONFIRMED = "STATEMENT_CONFIRMED"
    STATEMENT_FLAGGED = "STATEMENT_FLAGGED"
    STATEMENT_REJECTED = "STATEMENT_REJECTED"
    REVIEW_APPROVED = "REVIEW_APPROVED"
    REVIEW_REJECTED = "REVIEW_REJECTED"
    STATEMENT_OVERRIDDEN = "STATEMENT_OVERRIDDEN"
    TRUST_UPDATED = "TRUST_UPDATED"
