"""
Inventory API — baseline management and stock queries.
"""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.models.product import Product
from app.models.statement import Statement
from app.models.enums import StatementStatus, DirectionEnum
from app.schemas.baseline import BaselineCreate
from app.dependencies import get_current_user, get_shop_or_404, require_shop_owner, require_shop_member
from app.services.inventory_service import calculate_stock, get_shop_inventory, set_baseline

router = APIRouter(tags=["inventory"])


@router.post("/api/v1/shops/{shop_id}/baseline")
async def create_baseline(
    shop_id: uuid.UUID,
    body: BaselineCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Set baseline stock for a product. OWNER only."""
    await get_shop_or_404(shop_id, db)
    await require_shop_owner(shop_id, current_user, db)

    # Verify product belongs to shop
    result = await db.execute(
        select(Product).where(Product.id == body.product_id, Product.shop_id == shop_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Product not found in this shop."},
        )

    baseline = await set_baseline(
        db=db,
        shop_id=shop_id,
        product_id=body.product_id,
        quantity=float(body.quantity),
        unit=body.unit,
        created_by_id=current_user.id,
        notes=body.notes,
    )
    await db.commit()
    await db.refresh(baseline)

    return {
        "success": True,
        "data": {
            "id": str(baseline.id),
            "shop_id": str(baseline.shop_id),
            "product_id": str(baseline.product_id),
            "quantity": float(baseline.quantity),
            "unit": baseline.unit,
            "created_by_id": str(baseline.created_by_id),
            "is_superseded": baseline.is_superseded,
            "notes": baseline.notes,
            "created_at": baseline.created_at.isoformat(),
        },
    }


@router.get("/api/v1/shops/{shop_id}/inventory")
async def get_inventory(
    shop_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current stock for all products in a shop."""
    await get_shop_or_404(shop_id, db)
    await require_shop_member(shop_id, current_user, db)

    inventory = await get_shop_inventory(db, shop_id)
    return {"success": True, "data": inventory}


@router.get("/api/v1/products/{product_id}/inventory")
async def get_product_inventory(
    product_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current stock for a specific product."""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Product not found."})

    await require_shop_member(product.shop_id, current_user, db)

    stock = await calculate_stock(db, product.shop_id, product_id)
    return {"success": True, "data": {"product_name": product.name, "default_unit": product.default_unit, **stock}}


@router.get("/api/v1/products/{product_id}/history")
async def get_product_history(
    product_id: uuid.UUID,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get confirmed statement history for a product."""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Product not found."})

    await require_shop_member(product.shop_id, current_user, db)

    hist_result = await db.execute(
        select(Statement).where(
            Statement.product_id == product_id,
            Statement.status == StatementStatus.CONFIRMED,
        ).order_by(Statement.created_at.desc()).limit(limit).offset(offset)
    )
    statements = hist_result.scalars().all()

    return {
        "success": True,
        "data": [
            {
                "id": str(s.id),
                "quantity": float(s.quantity) if s.quantity else None,
                "unit": s.unit,
                "direction": s.direction.value if s.direction else None,
                "actor_id": str(s.actor_id) if s.actor_id else None,
                "transcript": s.transcript,
                "created_at": s.created_at.isoformat(),
                "event_time": s.event_time.isoformat() if s.event_time else None,
            }
            for s in statements
        ],
    }
