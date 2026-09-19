"""
Plausibility engine — deterministic quantity plausibility check.

Compares incoming quantity against historical shop patterns.
LLM does NOT decide plausibility — this is pure database logic.
"""
import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.statement import Statement
from app.models.enums import StatementStatus, DirectionEnum

# If quantity exceeds N standard deviations from mean, flag as implausible
STD_THRESHOLD = 3.0
# If fewer than this many historical statements, use upper bound multiplier
MIN_HISTORY_COUNT = 3
UPPER_BOUND_MULTIPLIER = 10.0  # Flag if > 10x the average


class PlausibilityResult:
    def __init__(
        self,
        passed: bool,
        reason: str,
        mean: Optional[float],
        std: Optional[float],
        historical_count: int,
    ):
        self.passed = passed
        self.reason = reason
        self.mean = mean
        self.std = std
        self.historical_count = historical_count

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "reason": self.reason,
            "mean": self.mean,
            "std": self.std,
            "historical_count": self.historical_count,
        }


async def check_plausibility(
    db: AsyncSession,
    shop_id: uuid.UUID,
    product_id: Optional[uuid.UUID],
    quantity: float,
    direction: str,
) -> PlausibilityResult:
    """
    Check if quantity is plausible given historical shop patterns.
    Deterministic — no LLM involvement.
    """
    if not product_id:
        return PlausibilityResult(
            passed=True,
            reason="No product resolved — cannot check history.",
            mean=None,
            std=None,
            historical_count=0,
        )

    # Get historical confirmed statements for this product + direction
    dir_enum = DirectionEnum.IN if direction == "IN" else DirectionEnum.OUT

    result = await db.execute(
        select(
            func.count(Statement.id).label("count"),
            func.avg(Statement.quantity).label("mean"),
            func.stddev(Statement.quantity).label("std"),
            func.max(Statement.quantity).label("max_qty"),
        ).where(
            Statement.shop_id == shop_id,
            Statement.product_id == product_id,
            Statement.direction == dir_enum,
            Statement.status == StatementStatus.CONFIRMED,
        )
    )
    row = result.one()
    count = int(row.count or 0)
    mean = float(row.mean) if row.mean else None
    std = float(row.std) if row.std else None
    max_qty = float(row.max_qty) if row.max_qty else None

    if count < MIN_HISTORY_COUNT:
        # Not enough history — use a simple upper bound heuristic
        if mean and quantity > mean * UPPER_BOUND_MULTIPLIER:
            return PlausibilityResult(
                passed=False,
                reason=f"Quantity {quantity} is {quantity/mean:.1f}x the historical average ({mean:.1f}) with limited history.",
                mean=mean,
                std=None,
                historical_count=count,
            )
        return PlausibilityResult(
            passed=True,
            reason=f"Insufficient history ({count} records) to check plausibility precisely.",
            mean=mean,
            std=None,
            historical_count=count,
        )

    # Statistical check: flag if outside mean ± N * std
    if std and std > 0:
        z_score = abs(quantity - mean) / std
        if z_score > STD_THRESHOLD:
            return PlausibilityResult(
                passed=False,
                reason=f"Quantity {quantity} is {z_score:.1f} standard deviations from the mean ({mean:.1f} ± {std:.1f}).",
                mean=mean,
                std=std,
                historical_count=count,
            )
    elif mean:
        # No variance in history — use multiplier check
        if quantity > mean * UPPER_BOUND_MULTIPLIER:
            return PlausibilityResult(
                passed=False,
                reason=f"Quantity {quantity} is significantly higher than the historical mean ({mean:.1f}).",
                mean=mean,
                std=std,
                historical_count=count,
            )

    return PlausibilityResult(
        passed=True,
        reason=f"Quantity {quantity} is within normal range (mean: {mean:.1f if mean else 'N/A'}).",
        mean=mean,
        std=std,
        historical_count=count,
    )
