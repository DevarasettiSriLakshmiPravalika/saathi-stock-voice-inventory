"""
Statement service — creates and manages the append-only statement ledger.
"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.statement import Statement
from app.models.statement_processing import StatementProcessing
from app.models.review import Review
from app.models.audit_log import AuditLog
from app.models.enums import StatementStatus, DecisionEnum, StatementSource, AuditAction, ReviewStatus


async def create_statement(
    db: AsyncSession,
    shop_id: uuid.UUID,
    actor_id: Optional[uuid.UUID],
    voice_profile_id: Optional[uuid.UUID],
    product_id: Optional[uuid.UUID],
    speaker_status: str,
    speaker_confidence: float,
    transcript: Optional[str],
    raw_claim: Optional[dict],
    quantity: Optional[float],
    unit: Optional[str],
    direction: Optional[str],
    decision: str,
    source: str = "MOBILE_WEB",
) -> Statement:
    """Create an immutable statement record in the ledger."""
    from app.models.enums import SpeakerStatus, DirectionEnum

    # Map decision to status
    if decision == "AUTO_CONFIRMED":
        status = StatementStatus.CONFIRMED
    elif decision == "REQUIRES_REVIEW":
        status = StatementStatus.FLAGGED
    else:
        status = StatementStatus.REJECTED

    stmt = Statement(
        shop_id=shop_id,
        actor_id=actor_id,
        voice_profile_id=voice_profile_id,
        product_id=product_id,
        speaker_status=SpeakerStatus(speaker_status),
        speaker_confidence=speaker_confidence,
        transcript=transcript,
        raw_claim=raw_claim,
        quantity=Decimal(str(quantity)) if quantity is not None else None,
        unit=unit,
        direction=DirectionEnum(direction) if direction else None,
        status=status,
        decision=DecisionEnum(decision),
        source=StatementSource(source),
        is_overridden=False,
    )
    db.add(stmt)
    await db.flush()

    # Audit
    audit_action = AuditAction.STATEMENT_CONFIRMED if status == StatementStatus.CONFIRMED else \
                   AuditAction.STATEMENT_FLAGGED if status == StatementStatus.FLAGGED else \
                   AuditAction.STATEMENT_REJECTED
    audit = AuditLog(
        shop_id=shop_id,
        actor_id=actor_id,
        action=AuditAction.STATEMENT_CREATED.value,
        entity_type="statement",
        entity_id=stmt.id,
    )
    db.add(audit)

    return stmt


async def create_statement_processing(
    db: AsyncSession,
    statement_id: uuid.UUID,
    asr_provider: Optional[str] = None,
    asr_confidence: Optional[float] = None,
    asr_language: Optional[str] = None,
    speaker_model_version: Optional[str] = None,
    speaker_confidence: Optional[float] = None,
    llm_provider: Optional[str] = None,
    trust_score: Optional[float] = None,
    trust_result: Optional[dict] = None,
    plausibility_passed: Optional[bool] = None,
    plausibility_result: Optional[dict] = None,
    contradiction_detected: Optional[bool] = None,
    contradiction_result: Optional[dict] = None,
    decision_explanation: Optional[str] = None,
    started_at: Optional[datetime] = None,
    completed_at: Optional[datetime] = None,
) -> StatementProcessing:
    """Create processing metadata record for a statement."""
    from decimal import Decimal

    processing = StatementProcessing(
        statement_id=statement_id,
        asr_provider=asr_provider,
        asr_confidence=Decimal(str(asr_confidence)) if asr_confidence is not None else None,
        asr_language=asr_language,
        asr_started_at=started_at,
        asr_completed_at=completed_at,
        speaker_model_version=speaker_model_version,
        speaker_confidence=Decimal(str(speaker_confidence)) if speaker_confidence is not None else None,
        llm_provider=llm_provider,
        trust_score=Decimal(str(trust_score)) if trust_score is not None else None,
        trust_result=trust_result,
        plausibility_passed=plausibility_passed,
        plausibility_result=plausibility_result,
        contradiction_detected=contradiction_detected,
        contradiction_result=contradiction_result,
        decision_explanation=decision_explanation,
        pipeline_started_at=started_at,
        pipeline_completed_at=completed_at,
    )
    db.add(processing)
    await db.flush()
    return processing


async def create_review_if_needed(
    db: AsyncSession,
    statement: Statement,
) -> Optional[Review]:
    """Create a review record if statement requires review."""
    if statement.status == StatementStatus.FLAGGED:
        review = Review(
            statement_id=statement.id,
            shop_id=statement.shop_id,
            status=ReviewStatus.PENDING,
        )
        db.add(review)
        await db.flush()
        return review
    return None


async def get_statement(db: AsyncSession, statement_id: uuid.UUID) -> Optional[Statement]:
    result = await db.execute(select(Statement).where(Statement.id == statement_id))
    return result.scalar_one_or_none()
