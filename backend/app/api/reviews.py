"""
Reviews API — owner review queue for flagged statements.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.models.review import Review
from app.models.statement import Statement
from app.models.statement_processing import StatementProcessing
from app.models.audit_log import AuditLog
from app.models.enums import ReviewStatus, ReviewDecision, StatementStatus, AuditAction
from app.dependencies import get_current_user, require_shop_owner, require_shop_member
from app.services.trust_service import record_trust_event

router = APIRouter(prefix="/api/v1/reviews", tags=["reviews"])


def _review_dict(r: Review, statement: Optional[Statement] = None, processing: Optional[StatementProcessing] = None) -> dict:
    d = {
        "id": str(r.id),
        "statement_id": str(r.statement_id),
        "shop_id": str(r.shop_id),
        "reviewer_id": str(r.reviewer_id) if r.reviewer_id else None,
        "status": r.status.value,
        "decision": r.decision.value if r.decision else None,
        "reason": r.reason,
        "completed_at": r.completed_at.isoformat() if r.completed_at else None,
        "created_at": r.created_at.isoformat(),
        "updated_at": r.updated_at.isoformat(),
    }
    if statement:
        d["statement"] = {
            "transcript": statement.transcript,
            "speaker_status": statement.speaker_status.value,
            "speaker_confidence": float(statement.speaker_confidence) if statement.speaker_confidence else None,
            "product_id": str(statement.product_id) if statement.product_id else None,
            "quantity": float(statement.quantity) if statement.quantity else None,
            "unit": statement.unit,
            "direction": statement.direction.value if statement.direction else None,
            "raw_claim": statement.raw_claim,
        }
    if processing:
        d["processing"] = {
            "trust_score": float(processing.trust_score) if processing.trust_score else None,
            "plausibility_passed": processing.plausibility_passed,
            "plausibility_result": processing.plausibility_result,
            "contradiction_detected": processing.contradiction_detected,
            "contradiction_result": processing.contradiction_result,
            "decision_explanation": processing.decision_explanation,
        }
    return d


@router.get("")
async def list_reviews(
    shop_id: uuid.UUID = Query(...),
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await require_shop_member(shop_id, current_user, db)

    query = select(Review).where(Review.shop_id == shop_id)
    if status_filter:
        try:
            query = query.where(Review.status == ReviewStatus(status_filter))
        except ValueError:
            raise HTTPException(400, detail={"code": "VALIDATION_ERROR", "message": f"Invalid status: {status_filter}"})

    query = query.order_by(Review.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    reviews = result.scalars().all()

    return {
        "success": True,
        "data": [_review_dict(r) for r in reviews],
        "count": len(reviews),
    }


@router.get("/{review_id}")
async def get_review(
    review_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Review).where(Review.id == review_id))
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Review not found."})

    await require_shop_member(review.shop_id, current_user, db)

    # Load statement and processing
    stmt_result = await db.execute(select(Statement).where(Statement.id == review.statement_id))
    statement = stmt_result.scalar_one_or_none()

    proc_result = await db.execute(
        select(StatementProcessing).where(StatementProcessing.statement_id == review.statement_id)
    )
    processing = proc_result.scalar_one_or_none()

    return {"success": True, "data": _review_dict(review, statement, processing)}


@router.post("/{review_id}/approve")
async def approve_review(
    review_id: uuid.UUID,
    body: dict = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Approve a review → statement becomes CONFIRMED → inventory updated.
    """
    body = body or {}
    review = await _get_pending_review(review_id, db)
    await require_shop_owner(review.shop_id, current_user, db)

    # Update review
    review.status = ReviewStatus.COMPLETED
    review.decision = ReviewDecision.APPROVED
    review.reviewer_id = current_user.id
    review.reason = body.get("reason")
    review.completed_at = datetime.now(timezone.utc)

    # Confirm the statement — inventory now reflects this
    stmt_result = await db.execute(select(Statement).where(Statement.id == review.statement_id))
    statement = stmt_result.scalar_one_or_none()
    if statement:
        statement.status = StatementStatus.CONFIRMED

    # Trust update — approval boosts trust
    if statement and statement.actor_id:
        proc_result = await db.execute(
            select(StatementProcessing).where(StatementProcessing.statement_id == statement.id)
        )
        proc = proc_result.scalar_one_or_none()
        current_trust = float(proc.trust_score) if proc and proc.trust_score else 0.5
        new_trust = min(1.0, current_trust + 0.05)
        await record_trust_event(
            db=db,
            shop_id=review.shop_id,
            user_id=statement.actor_id,
            new_score=new_trust,
            trigger_event="REVIEW_APPROVED",
            statement_id=statement.id,
            review_id=review.id,
            reason="Review approved by owner",
        )

    audit = AuditLog(
        shop_id=review.shop_id,
        actor_id=current_user.id,
        action=AuditAction.REVIEW_APPROVED.value,
        entity_type="review",
        entity_id=review.id,
        metadata_={"statement_id": str(review.statement_id)},
    )
    db.add(audit)
    await db.commit()

    return {
        "success": True,
        "data": {
            "review_id": str(review.id),
            "decision": "APPROVED",
            "statement_status": "CONFIRMED",
            "message": "Statement confirmed. Inventory updated.",
        },
    }


@router.post("/{review_id}/reject")
async def reject_review(
    review_id: uuid.UUID,
    body: dict = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Reject a review → statement stays REJECTED → inventory unchanged.
    """
    body = body or {}
    review = await _get_pending_review(review_id, db)
    await require_shop_owner(review.shop_id, current_user, db)

    review.status = ReviewStatus.COMPLETED
    review.decision = ReviewDecision.REJECTED
    review.reviewer_id = current_user.id
    review.reason = body.get("reason")
    review.completed_at = datetime.now(timezone.utc)

    # Mark statement as rejected
    stmt_result = await db.execute(select(Statement).where(Statement.id == review.statement_id))
    statement = stmt_result.scalar_one_or_none()
    if statement:
        statement.status = StatementStatus.REJECTED

    # Trust update — rejection penalizes trust
    if statement and statement.actor_id:
        proc_result = await db.execute(
            select(StatementProcessing).where(StatementProcessing.statement_id == statement.id)
        )
        proc = proc_result.scalar_one_or_none()
        current_trust = float(proc.trust_score) if proc and proc.trust_score else 0.5
        new_trust = max(0.0, current_trust - 0.1)
        await record_trust_event(
            db=db,
            shop_id=review.shop_id,
            user_id=statement.actor_id,
            new_score=new_trust,
            trigger_event="REVIEW_REJECTED",
            statement_id=statement.id,
            review_id=review.id,
            reason="Review rejected by owner",
        )

    audit = AuditLog(
        shop_id=review.shop_id,
        actor_id=current_user.id,
        action=AuditAction.REVIEW_REJECTED.value,
        entity_type="review",
        entity_id=review.id,
        metadata_={"statement_id": str(review.statement_id)},
    )
    db.add(audit)
    await db.commit()

    return {
        "success": True,
        "data": {
            "review_id": str(review.id),
            "decision": "REJECTED",
            "statement_status": "REJECTED",
            "message": "Statement rejected. Inventory unchanged.",
        },
    }


async def _get_pending_review(review_id: uuid.UUID, db: AsyncSession) -> Review:
    result = await db.execute(select(Review).where(Review.id == review_id))
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Review not found."})
    if review.status == ReviewStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "VALIDATION_ERROR", "message": "Review is already completed."},
        )
    return review
