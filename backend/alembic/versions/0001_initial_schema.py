"""Initial Saathi database schema — Phase 1

Creates all core entities as defined in SAATHI_CONTRACT.md v1.0.0.

Tables created (in dependency order):
    users → shops → shop_members → products → voice_profiles
    → baselines → vocabulary_entries → statements
    → statement_processing → reviews → trust_history → audit_logs

Enum types are created explicitly before any tables.
Tables use postgresql.ENUM(..., create_type=False) to reference them
without triggering a second CREATE TYPE call.

Revision ID: 0001
Revises:
Create Date: 2026-09-19
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# ── Enum type definitions ──────────────────────────────────────────────────────
# Pre-defined with create_type=False so they can be used inside op.create_table
# without triggering automatic CREATE TYPE (we create them explicitly below).

user_role_enum = postgresql.ENUM(
    "OWNER", "STAFF", "OUTSIDER",
    name="user_role", create_type=False,
)
membership_status_enum = postgresql.ENUM(
    "ACTIVE", "INACTIVE",
    name="membership_status", create_type=False,
)
statement_status_enum = postgresql.ENUM(
    "PENDING", "PROCESSING", "CONFIRMED", "FLAGGED", "REJECTED",
    name="statement_status", create_type=False,
)
decision_enum = postgresql.ENUM(
    "AUTO_CONFIRMED", "REQUIRES_REVIEW", "REJECTED",
    name="decision_enum", create_type=False,
)
direction_enum = postgresql.ENUM(
    "IN", "OUT",
    name="direction_enum", create_type=False,
)
speaker_status_enum = postgresql.ENUM(
    "IDENTIFIED", "LOW_CONFIDENCE", "UNKNOWN",
    name="speaker_status", create_type=False,
)
voice_enrollment_status_enum = postgresql.ENUM(
    "ENROLLED", "LOW_QUALITY", "FAILED",
    name="voice_enrollment_status", create_type=False,
)
vocabulary_mapping_type_enum = postgresql.ENUM(
    "PRODUCT_ALIAS", "UNIT_ALIAS", "UNIT_CONVERSION",
    name="vocabulary_mapping_type", create_type=False,
)
review_status_enum = postgresql.ENUM(
    "PENDING", "COMPLETED",
    name="review_status", create_type=False,
)
review_decision_enum = postgresql.ENUM(
    "APPROVED", "REJECTED", "OVERRIDDEN",
    name="review_decision", create_type=False,
)
statement_source_enum = postgresql.ENUM(
    "MOBILE_WEB", "LIVE_MIC", "PHONE_CALL", "MANUAL",
    name="statement_source", create_type=False,
)


def upgrade() -> None:
    # ── 1. Create all enum types explicitly ───────────────────────────────────
    # We use checkfirst=True to be safe against partially-applied migrations.
    # All table columns below use create_type=False to prevent duplicate CREATE.
    bind = op.get_bind()
    postgresql.ENUM("OWNER", "STAFF", "OUTSIDER",
                    name="user_role").create(bind, checkfirst=True)
    postgresql.ENUM("ACTIVE", "INACTIVE",
                    name="membership_status").create(bind, checkfirst=True)
    postgresql.ENUM("PENDING", "PROCESSING", "CONFIRMED", "FLAGGED", "REJECTED",
                    name="statement_status").create(bind, checkfirst=True)
    postgresql.ENUM("AUTO_CONFIRMED", "REQUIRES_REVIEW", "REJECTED",
                    name="decision_enum").create(bind, checkfirst=True)
    postgresql.ENUM("IN", "OUT",
                    name="direction_enum").create(bind, checkfirst=True)
    postgresql.ENUM("IDENTIFIED", "LOW_CONFIDENCE", "UNKNOWN",
                    name="speaker_status").create(bind, checkfirst=True)
    postgresql.ENUM("ENROLLED", "LOW_QUALITY", "FAILED",
                    name="voice_enrollment_status").create(bind, checkfirst=True)
    postgresql.ENUM("PRODUCT_ALIAS", "UNIT_ALIAS", "UNIT_CONVERSION",
                    name="vocabulary_mapping_type").create(bind, checkfirst=True)
    postgresql.ENUM("PENDING", "COMPLETED",
                    name="review_status").create(bind, checkfirst=True)
    postgresql.ENUM("APPROVED", "REJECTED", "OVERRIDDEN",
                    name="review_decision").create(bind, checkfirst=True)
    postgresql.ENUM("MOBILE_WEB", "LIVE_MIC", "PHONE_CALL", "MANUAL",
                    name="statement_source").create(bind, checkfirst=True)

    # ── 2. users ──────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False,
                  server_default=sa.text("true")),
        sa.Column("is_phone_verified", sa.Boolean(), nullable=False,
                  server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("phone", name="uq_users_phone"),
    )
    op.create_index("ix_users_phone", "users", ["phone"])

    # ── 3. shops ──────────────────────────────────────────────────────────────
    op.create_table(
        "shops",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False,
                  server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_shops_owner_id", "shops", ["owner_id"])

    # ── 4. shop_members ───────────────────────────────────────────────────────
    op.create_table(
        "shop_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("shop_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", user_role_enum, nullable=False),
        sa.Column("status", membership_status_enum, nullable=False,
                  server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["shop_id"], ["shops.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("shop_id", "user_id", name="uq_shop_members_shop_user"),
    )
    op.create_index("ix_shop_members_shop_id", "shop_members", ["shop_id"])
    op.create_index("ix_shop_members_user_id", "shop_members", ["user_id"])

    # ── 5. products ───────────────────────────────────────────────────────────
    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("shop_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("default_unit", sa.String(100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False,
                  server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["shop_id"], ["shops.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("shop_id", "name", name="uq_products_shop_name"),
    )
    op.create_index("ix_products_shop_id", "products", ["shop_id"])

    # ── 6. voice_profiles ─────────────────────────────────────────────────────
    op.create_table(
        "voice_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("shop_id", postgresql.UUID(as_uuid=True), nullable=False),
        # embedding: sensitive biometric data — NEVER expose via API
        sa.Column("embedding", postgresql.JSONB(), nullable=True),
        sa.Column("enrollment_status", voice_enrollment_status_enum,
                  nullable=False, server_default="FAILED"),
        sa.Column("quality_score", sa.Float(), nullable=True),
        sa.Column("audio_duration_seconds", sa.Float(), nullable=True),
        sa.Column("model_version", sa.String(100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["shop_id"], ["shops.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_voice_profiles_user_id", "voice_profiles", ["user_id"])
    op.create_index("ix_voice_profiles_shop_id", "voice_profiles", ["shop_id"])

    # ── 7. baselines ──────────────────────────────────────────────────────────
    op.create_table(
        "baselines",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("shop_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("unit", sa.String(100), nullable=False),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("is_superseded", sa.Boolean(), nullable=False,
                  server_default=sa.text("false")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["shop_id"], ["shops.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_baselines_shop_id", "baselines", ["shop_id"])
    op.create_index("ix_baselines_product_id", "baselines", ["product_id"])
    op.create_index("ix_baselines_shop_product", "baselines", ["shop_id", "product_id"])

    # ── 8. vocabulary_entries ─────────────────────────────────────────────────
    op.create_table(
        "vocabulary_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("shop_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_term", sa.String(255), nullable=False),
        sa.Column("mapping_type", vocabulary_mapping_type_enum, nullable=False),
        sa.Column("target_product_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("target_unit", sa.String(100), nullable=True),
        sa.Column("conversion_factor", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False,
                  server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["shop_id"], ["shops.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["target_product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("shop_id", "source_term", "mapping_type",
                            name="uq_vocabulary_shop_term_type"),
    )
    op.create_index("ix_vocabulary_shop_id", "vocabulary_entries", ["shop_id"])

    # ── 9. statements (append-only ledger) ────────────────────────────────────
    op.create_table(
        "statements",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("shop_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("voice_profile_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("speaker_status", speaker_status_enum, nullable=False),
        sa.Column("speaker_confidence", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("transcript", sa.Text(), nullable=True),
        sa.Column("raw_claim", postgresql.JSONB(), nullable=True),
        sa.Column("quantity", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column("unit", sa.String(100), nullable=True),
        sa.Column("direction", direction_enum, nullable=True),
        sa.Column("status", statement_status_enum,
                  nullable=False, server_default="PENDING"),
        sa.Column("decision", decision_enum, nullable=True),
        sa.Column("source", statement_source_enum,
                  nullable=False, server_default="MOBILE_WEB"),
        sa.Column("is_overridden", sa.Boolean(), nullable=False,
                  server_default=sa.text("false")),
        sa.Column("override_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("override_reason", sa.Text(), nullable=True),
        sa.Column("override_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("event_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["shop_id"], ["shops.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["voice_profile_id"], ["voice_profiles.id"],
                                ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["override_by_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_statements_shop_id", "statements", ["shop_id"])
    op.create_index("ix_statements_product_id", "statements", ["product_id"])
    op.create_index("ix_statements_actor_id", "statements", ["actor_id"])
    op.create_index("ix_statements_status", "statements", ["status"])
    op.create_index("ix_statements_decision", "statements", ["decision"])
    op.create_index("ix_statements_created_at", "statements", ["created_at"])
    op.create_index("ix_statements_shop_status", "statements", ["shop_id", "status"])
    op.create_index("ix_statements_shop_created", "statements", ["shop_id", "created_at"])

    # ── 10. statement_processing ──────────────────────────────────────────────
    op.create_table(
        "statement_processing",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("statement_id", postgresql.UUID(as_uuid=True), nullable=False,
                  unique=True),
        sa.Column("asr_provider", sa.String(100), nullable=True),
        sa.Column("asr_confidence", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("asr_language", sa.String(20), nullable=True),
        sa.Column("asr_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("asr_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("speaker_model_version", sa.String(100), nullable=True),
        sa.Column("speaker_confidence", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("speaker_identification_started_at",
                  sa.DateTime(timezone=True), nullable=True),
        sa.Column("speaker_identification_completed_at",
                  sa.DateTime(timezone=True), nullable=True),
        sa.Column("llm_provider", sa.String(100), nullable=True),
        sa.Column("llm_model", sa.String(100), nullable=True),
        sa.Column("claim_confidence", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("claim_extraction_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("claim_extraction_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("trust_score", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("trust_result", postgresql.JSONB(), nullable=True),
        sa.Column("plausibility_passed", sa.Boolean(), nullable=True),
        sa.Column("plausibility_result", postgresql.JSONB(), nullable=True),
        sa.Column("contradiction_detected", sa.Boolean(), nullable=True),
        sa.Column("contradiction_result", postgresql.JSONB(), nullable=True),
        sa.Column("pipeline_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("pipeline_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processing_errors", postgresql.JSONB(), nullable=True),
        sa.Column("decision_explanation", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["statement_id"], ["statements.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_statement_processing_statement_id",
                    "statement_processing", ["statement_id"])

    # ── 11. reviews ───────────────────────────────────────────────────────────
    op.create_table(
        "reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("statement_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("shop_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reviewer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", review_status_enum, nullable=False, server_default="PENDING"),
        sa.Column("decision", review_decision_enum, nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["statement_id"], ["statements.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["shop_id"], ["shops.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["reviewer_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reviews_shop_id", "reviews", ["shop_id"])
    op.create_index("ix_reviews_statement_id", "reviews", ["statement_id"])
    op.create_index("ix_reviews_status", "reviews", ["status"])
    op.create_index("ix_reviews_shop_status", "reviews", ["shop_id", "status"])

    # ── 12. trust_history ─────────────────────────────────────────────────────
    op.create_table(
        "trust_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("shop_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("previous_trust_score", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("new_trust_score", sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column("trigger_event", sa.String(100), nullable=False),
        sa.Column("related_statement_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("related_review_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["shop_id"], ["shops.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["related_statement_id"], ["statements.id"],
                                ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["related_review_id"], ["reviews.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_trust_history_shop_id", "trust_history", ["shop_id"])
    op.create_index("ix_trust_history_user_id", "trust_history", ["user_id"])
    op.create_index("ix_trust_history_shop_user", "trust_history", ["shop_id", "user_id"])

    # ── 13. audit_logs ────────────────────────────────────────────────────────
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("shop_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=True),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["shop_id"], ["shops.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_shop_id", "audit_logs", ["shop_id"])
    op.create_index("ix_audit_logs_actor_id", "audit_logs", ["actor_id"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])
    op.create_index("ix_audit_logs_shop_created", "audit_logs", ["shop_id", "created_at"])


def downgrade() -> None:
    # Drop tables in REVERSE dependency order
    op.drop_table("audit_logs")
    op.drop_table("trust_history")
    op.drop_table("reviews")
    op.drop_table("statement_processing")
    op.drop_table("statements")
    op.drop_table("vocabulary_entries")
    op.drop_table("baselines")
    op.drop_table("voice_profiles")
    op.drop_table("products")
    op.drop_table("shop_members")
    op.drop_table("shops")
    op.drop_table("users")

    # Drop enum types in reverse creation order
    bind = op.get_bind()
    postgresql.ENUM("MOBILE_WEB", "LIVE_MIC", "PHONE_CALL", "MANUAL",
                    name="statement_source").drop(bind, checkfirst=True)
    postgresql.ENUM("APPROVED", "REJECTED", "OVERRIDDEN",
                    name="review_decision").drop(bind, checkfirst=True)
    postgresql.ENUM("PENDING", "COMPLETED",
                    name="review_status").drop(bind, checkfirst=True)
    postgresql.ENUM("PRODUCT_ALIAS", "UNIT_ALIAS", "UNIT_CONVERSION",
                    name="vocabulary_mapping_type").drop(bind, checkfirst=True)
    postgresql.ENUM("ENROLLED", "LOW_QUALITY", "FAILED",
                    name="voice_enrollment_status").drop(bind, checkfirst=True)
    postgresql.ENUM("IDENTIFIED", "LOW_CONFIDENCE", "UNKNOWN",
                    name="speaker_status").drop(bind, checkfirst=True)
    postgresql.ENUM("IN", "OUT",
                    name="direction_enum").drop(bind, checkfirst=True)
    postgresql.ENUM("AUTO_CONFIRMED", "REQUIRES_REVIEW", "REJECTED",
                    name="decision_enum").drop(bind, checkfirst=True)
    postgresql.ENUM("PENDING", "PROCESSING", "CONFIRMED", "FLAGGED", "REJECTED",
                    name="statement_status").drop(bind, checkfirst=True)
    postgresql.ENUM("ACTIVE", "INACTIVE",
                    name="membership_status").drop(bind, checkfirst=True)
    postgresql.ENUM("OWNER", "STAFF", "OUTSIDER",
                    name="user_role").drop(bind, checkfirst=True)
