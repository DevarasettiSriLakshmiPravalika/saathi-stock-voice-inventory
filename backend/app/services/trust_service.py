"""
Trust engine — speaker trust evaluation (Contract §26 / §37).

Trust is:
- Shop-specific (not transferable between shops)
- Deterministic and auditable
- Based on historical statement outcomes
- Bounded 0.00 - 1.00

Trust is NOT decided by LLM.
"""
import uuid
from decimal import Decimal
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case, Integer

from app.models.statement import Statement
from app.models.trust_history import TrustHistory
from app.models.enums import StatementStatus

DEFAULT_TRUST = 0.5
MAX_TRUST = 1.0
MIN_TRUST = 0.0

# Trust adjustments per event
TRUST_BOOST_CONFIRMED = 0.05
TRUST_PENALTY_REJECTED = 0.1
TRUST_PENALTY_FLAGGED = 0.02

IDENTITY_WEIGHT = 0.3
HISTORY_WEIGHT = 0.7


class TrustResult:
    def __init__(
        self,
        score: float,
        components: dict,
    ):
        self.score = score
        self.components = components


async def calculate_trust(
    db: AsyncSession,
    shop_id: uuid.UUID,
    user_id: Optional[uuid.UUID],
    speaker_status: str,
    speaker_confidence: float,
) -> TrustResult:
    """
    Calculate speaker trust score for this shop interaction.
    Returns a TrustResult with bounded score and component breakdown.
    """
    # Identity confidence component
    identity_score = 0.0
    if speaker_status == "IDENTIFIED":
        identity_score = speaker_confidence
    elif speaker_status == "LOW_CONFIDENCE":
        identity_score = speaker_confidence * 0.5
    else:
        identity_score = 0.0

    # Historical reliability component
    history_score = DEFAULT_TRUST
    if user_id:
        result = await db.execute(
            select(
                func.count(Statement.id).label("total"),
                func.sum(
                    case((Statement.status == StatementStatus.CONFIRMED, 1), else_=0)
                ).label("confirmed"),
                func.sum(
                    case((Statement.status == StatementStatus.REJECTED, 1), else_=0)
                ).label("rejected"),
            ).where(
                Statement.shop_id == shop_id,
                Statement.actor_id == user_id,
            )
        )
        row = result.one()
        total = row.total or 0
        confirmed = int(row.confirmed or 0)
        rejected = int(row.rejected or 0)

        if total > 0:
            reliability = confirmed / total
            # Adjust base score based on history volume
            history_score = 0.3 + (reliability * 0.7)
            # Penalize high rejection rate
            if total >= 5 and rejected / total > 0.3:
                history_score *= 0.7

        # Get latest trust_history score as baseline if available
        th_result = await db.execute(
            select(TrustHistory).where(
                TrustHistory.shop_id == shop_id,
                TrustHistory.user_id == user_id,
            ).order_by(TrustHistory.occurred_at.desc()).limit(1)
        )
        latest_th = th_result.scalar_one_or_none()
        if latest_th:
            # Blend historical with current computation
            history_score = (float(latest_th.new_trust_score) + history_score) / 2

    # Combined score
    combined = (identity_score * IDENTITY_WEIGHT) + (history_score * HISTORY_WEIGHT)
    final_score = max(MIN_TRUST, min(MAX_TRUST, combined))

    return TrustResult(
        score=round(final_score, 4),
        components={
            "identity_score": round(identity_score, 4),
            "history_score": round(history_score, 4),
            "speaker_status": speaker_status,
            "speaker_confidence": speaker_confidence,
        },
    )


async def record_trust_event(
    db: AsyncSession,
    shop_id: uuid.UUID,
    user_id: uuid.UUID,
    new_score: float,
    trigger_event: str,
    statement_id: Optional[uuid.UUID] = None,
    review_id: Optional[uuid.UUID] = None,
    reason: Optional[str] = None,
):
    """Record a trust change in the append-only trust history."""
    # Get previous score
    result = await db.execute(
        select(TrustHistory).where(
            TrustHistory.shop_id == shop_id,
            TrustHistory.user_id == user_id,
        ).order_by(TrustHistory.occurred_at.desc()).limit(1)
    )
    latest = result.scalar_one_or_none()
    previous_score = float(latest.new_trust_score) if latest else None

    entry = TrustHistory(
        shop_id=shop_id,
        user_id=user_id,
        previous_trust_score=previous_score,
        new_trust_score=Decimal(str(new_score)),
        trigger_event=trigger_event,
        related_statement_id=statement_id,
        related_review_id=review_id,
        reason=reason,
    )
    db.add(entry)
    await db.flush()
    return entry
