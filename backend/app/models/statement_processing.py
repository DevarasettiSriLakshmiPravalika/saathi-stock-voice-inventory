import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean, ForeignKey, Numeric, Text, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.statement import Statement


class StatementProcessing(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Processing pipeline metadata for a Statement (Contract §17).

    Purpose: debugging, auditing, observability, explainability.

    Pipeline stages tracked:
        Audio → Speaker ID → ASR → Claim Extraction → Entity Resolution
        → Unit Normalization → Trust Evaluation → Plausibility Check
        → Contradiction Check → Decision

    Security notes:
    - Raw audio is NOT stored here.
    - No sensitive biometric data is logged.
    - Internal model details (provider/version) may be stored for debugging.
    - decision_explanation must reflect ACTUAL backend evidence —
      not a hallucinated LLM explanation.
    """
    __tablename__ = "statement_processing"
    __table_args__ = (
        Index("ix_statement_processing_statement_id", "statement_id"),
    )

    # One processing record per statement
    statement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("statements.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    # ── ASR (Speech Recognition) ───────────────────────────────────────────────
    asr_provider: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    asr_confidence: Mapped[Optional[float]] = mapped_column(Numeric(precision=5, scale=4), nullable=True)
    asr_language: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    asr_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    asr_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # ── Speaker Identification ─────────────────────────────────────────────────
    speaker_model_version: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    speaker_confidence: Mapped[Optional[float]] = mapped_column(Numeric(precision=5, scale=4), nullable=True)
    speaker_identification_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    speaker_identification_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # ── Claim Extraction (LLM) ─────────────────────────────────────────────────
    llm_provider: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    llm_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    claim_confidence: Mapped[Optional[float]] = mapped_column(Numeric(precision=5, scale=4), nullable=True)
    claim_extraction_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    claim_extraction_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # ── Trust Evaluation ──────────────────────────────────────────────────────
    trust_score: Mapped[Optional[float]] = mapped_column(Numeric(precision=5, scale=4), nullable=True)
    trust_result: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # ── Plausibility Check ────────────────────────────────────────────────────
    plausibility_passed: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    plausibility_result: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # ── Contradiction Check ───────────────────────────────────────────────────
    contradiction_detected: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    contradiction_result: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # ── Overall Pipeline ───────────────────────────────────────────────────────
    pipeline_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    pipeline_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    processing_errors: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Decision explanation — must reflect actual backend evidence, not LLM output
    decision_explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    statement: Mapped["Statement"] = relationship("Statement", back_populates="processing")
