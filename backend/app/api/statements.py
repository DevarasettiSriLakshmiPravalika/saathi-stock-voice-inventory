"""
Statements API — list and retrieve statement ledger records.
"""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.models.statement import Statement
from app.models.statement_processing import StatementProcessing
from app.models.enums import StatementStatus, DecisionEnum, DirectionEnum, AuditAction
from app.dependencies import get_current_user, require_shop_member

router = APIRouter(prefix="/api/v1/statements", tags=["statements"])


def _statement_dict(s: Statement, processing: Optional[StatementProcessing] = None) -> dict:
    d = {
        "id": str(s.id),
        "shop_id": str(s.shop_id),
        "actor_id": str(s.actor_id) if s.actor_id else None,
        "product_id": str(s.product_id) if s.product_id else None,
        "voice_profile_id": str(s.voice_profile_id) if s.voice_profile_id else None,
        "speaker_status": s.speaker_status.value,
        "speaker_confidence": float(s.speaker_confidence) if s.speaker_confidence else None,
        "transcript": s.transcript,
        "raw_claim": s.raw_claim,
        "quantity": float(s.quantity) if s.quantity else None,
        "unit": s.unit,
        "direction": s.direction.value if s.direction else None,
        "status": s.status.value,
        "decision": s.decision.value if s.decision else None,
        "source": s.source.value,
        "is_overridden": s.is_overridden,
        "override_reason": s.override_reason,
        "override_at": s.override_at.isoformat() if s.override_at else None,
        "event_time": s.event_time.isoformat() if s.event_time else None,
        "created_at": s.created_at.isoformat(),
        "updated_at": s.updated_at.isoformat(),
    }
    if processing:
        d["processing"] = {
            "trust_score": float(processing.trust_score) if processing.trust_score else None,
            "plausibility_passed": processing.plausibility_passed,
            "contradiction_detected": processing.contradiction_detected,
            "decision_explanation": processing.decision_explanation,
            "asr_provider": processing.asr_provider,
            "asr_language": processing.asr_language,
        }
    return d


@router.get("")
async def list_statements(
    shop_id: uuid.UUID = Query(...),
    product_id: Optional[uuid.UUID] = Query(None),
    actor_id: Optional[uuid.UUID] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    direction: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await require_shop_member(shop_id, current_user, db)

    query = select(Statement).where(Statement.shop_id == shop_id)

    if product_id:
        query = query.where(Statement.product_id == product_id)
    if actor_id:
        query = query.where(Statement.actor_id == actor_id)
    if status_filter:
        try:
            query = query.where(Statement.status == StatementStatus(status_filter))
        except ValueError:
            raise HTTPException(400, detail={"code": "VALIDATION_ERROR", "message": f"Invalid status: {status_filter}"})
    if direction:
        try:
            query = query.where(Statement.direction == DirectionEnum(direction))
        except ValueError:
            raise HTTPException(400, detail={"code": "VALIDATION_ERROR", "message": f"Invalid direction: {direction}"})

    query = query.order_by(Statement.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    statements = result.scalars().all()

    return {
        "success": True,
        "data": [_statement_dict(s) for s in statements],
        "count": len(statements),
        "offset": offset,
        "limit": limit,
    }


@router.get("/{statement_id}")
async def get_statement(
    statement_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Statement).where(Statement.id == statement_id))
    statement = result.scalar_one_or_none()
    if not statement:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Statement not found."})

    await require_shop_member(statement.shop_id, current_user, db)

    # Load processing
    proc_result = await db.execute(
        select(StatementProcessing).where(StatementProcessing.statement_id == statement_id)
    )
    processing = proc_result.scalar_one_or_none()

    return {"success": True, "data": _statement_dict(statement, processing)}


@router.post("/{statement_id}/override")
async def override_statement(
    statement_id: uuid.UUID,
    body: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Owner can override statement fields.
    Original data preserved — override is additive.
    Creates audit record.
    """
    from app.dependencies import require_shop_owner
    from app.models.audit_log import AuditLog
    from app.models.enums import AuditAction, StatementStatus, DecisionEnum, DirectionEnum
    from decimal import Decimal
    from datetime import datetime, timezone

    result = await db.execute(select(Statement).where(Statement.id == statement_id))
    statement = result.scalar_one_or_none()
    if not statement:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Statement not found."})

    await require_shop_owner(statement.shop_id, current_user, db)

    original = {
        "product_id": str(statement.product_id) if statement.product_id else None,
        "quantity": float(statement.quantity) if statement.quantity else None,
        "unit": statement.unit,
        "direction": statement.direction.value if statement.direction else None,
        "status": statement.status.value,
        "actor_id": str(statement.actor_id) if statement.actor_id else None,
    }

    # Apply overrides
    if "product_id" in body and body["product_id"]:
        statement.product_id = uuid.UUID(str(body["product_id"]))
    if "quantity" in body and body["quantity"] is not None:
        statement.quantity = Decimal(str(body["quantity"]))
    if "unit" in body and body["unit"]:
        statement.unit = body["unit"]
    if "direction" in body and body["direction"]:
        statement.direction = DirectionEnum(body["direction"])
    if "actor_id" in body and body["actor_id"]:
        statement.actor_id = uuid.UUID(str(body["actor_id"]))
    if "status" in body and body["status"]:
        statement.status = StatementStatus(body["status"])
        if body["status"] == "CONFIRMED" and not statement.decision:
            statement.decision = DecisionEnum.AUTO_CONFIRMED

    statement.is_overridden = True
    statement.override_by_id = current_user.id
    statement.override_reason = body.get("reason", "Owner override")
    statement.override_at = datetime.now(timezone.utc)

    audit = AuditLog(
        shop_id=statement.shop_id,
        actor_id=current_user.id,
        action=AuditAction.STATEMENT_OVERRIDDEN.value,
        entity_type="statement",
        entity_id=statement.id,
        metadata_={
            "original": original,
            "reason": statement.override_reason,
        },
    )
    db.add(audit)
    await db.commit()
    await db.refresh(statement)

    return {"success": True, "data": _statement_dict(statement)}
