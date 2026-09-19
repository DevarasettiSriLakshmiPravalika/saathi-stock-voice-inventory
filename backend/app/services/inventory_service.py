"""
Inventory service — calculate stock from baseline + confirmed statements.

FORMULA: Current Stock = Latest Baseline + SUM(CONFIRMED IN) - SUM(CONFIRMED OUT)

CRITICAL:
- NEVER use Product.current_stock (no such column).
- Only CONFIRMED statements affect inventory.
- PENDING, PROCESSING, FLAGGED, REJECTED do NOT affect stock.
"""
import uuid
from decimal import Decimal
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.baseline import Baseline
from app.models.statement import Statement
from app.models.product import Product
from app.models.enums import StatementStatus, DirectionEnum


async def calculate_stock(
    db: AsyncSession,
    shop_id: uuid.UUID,
    product_id: uuid.UUID,
) -> dict:
    """
    Calculate current stock for a product.
    Returns dict with stock details.
    """
    # Get latest non-superseded baseline
    baseline_result = await db.execute(
        select(Baseline).where(
            Baseline.shop_id == shop_id,
            Baseline.product_id == product_id,
            Baseline.is_superseded == False,
        ).order_by(Baseline.created_at.desc()).limit(1)
    )
    baseline = baseline_result.scalar_one_or_none()

    if not baseline:
        return {
            "product_id": str(product_id),
            "current_stock": None,
            "baseline_quantity": None,
            "confirmed_in": 0.0,
            "confirmed_out": 0.0,
            "unit": None,
            "has_baseline": False,
        }

    baseline_qty = float(baseline.quantity)
    baseline_time = baseline.created_at

    # Sum CONFIRMED IN after baseline
    in_result = await db.execute(
        select(func.coalesce(func.sum(Statement.quantity), 0)).where(
            Statement.shop_id == shop_id,
            Statement.product_id == product_id,
            Statement.direction == DirectionEnum.IN,
            Statement.status == StatementStatus.CONFIRMED,
            Statement.created_at > baseline_time,
        )
    )
    in_total = float(in_result.scalar() or 0)

    # Sum CONFIRMED OUT after baseline
    out_result = await db.execute(
        select(func.coalesce(func.sum(Statement.quantity), 0)).where(
            Statement.shop_id == shop_id,
            Statement.product_id == product_id,
            Statement.direction == DirectionEnum.OUT,
            Statement.status == StatementStatus.CONFIRMED,
            Statement.created_at > baseline_time,
        )
    )
    out_total = float(out_result.scalar() or 0)

    current_stock = baseline_qty + in_total - out_total

    return {
        "product_id": str(product_id),
        "current_stock": round(current_stock, 4),
        "baseline_quantity": baseline_qty,
        "confirmed_in": in_total,
        "confirmed_out": out_total,
        "unit": baseline.unit,
        "has_baseline": True,
        "baseline_date": baseline.created_at.isoformat(),
    }


async def get_shop_inventory(
    db: AsyncSession,
    shop_id: uuid.UUID,
) -> list[dict]:
    """Get current stock for all active products in a shop."""
    result = await db.execute(
        select(Product).where(
            Product.shop_id == shop_id,
            Product.is_active == True,
        ).order_by(Product.name)
    )
    products = result.scalars().all()

    inventory = []
    for product in products:
        stock = await calculate_stock(db, shop_id, product.id)
        inventory.append({
            "product_id": str(product.id),
            "product_name": product.name,
            "default_unit": product.default_unit,
            **stock,
        })

    return inventory


async def set_baseline(
    db: AsyncSession,
    shop_id: uuid.UUID,
    product_id: uuid.UUID,
    quantity: float,
    unit: str,
    created_by_id: uuid.UUID,
    notes: Optional[str] = None,
) -> Baseline:
    """
    Set a new baseline for a product.
    Supersedes the previous baseline.
    """
    from app.models.audit_log import AuditLog
    from app.models.enums import AuditAction

    # Supersede existing baseline
    existing_result = await db.execute(
        select(Baseline).where(
            Baseline.shop_id == shop_id,
            Baseline.product_id == product_id,
            Baseline.is_superseded == False,
        )
    )
    for existing in existing_result.scalars().all():
        existing.is_superseded = True

    baseline = Baseline(
        shop_id=shop_id,
        product_id=product_id,
        quantity=Decimal(str(quantity)),
        unit=unit,
        created_by_id=created_by_id,
        is_superseded=False,
        notes=notes,
    )
    db.add(baseline)
    await db.flush()

    audit = AuditLog(
        shop_id=shop_id,
        actor_id=created_by_id,
        action=AuditAction.BASELINE_CREATED.value,
        entity_type="baseline",
        entity_id=baseline.id,
        metadata_={"product_id": str(product_id), "quantity": quantity, "unit": unit},
    )
    db.add(audit)
    await db.flush()

    return baseline
