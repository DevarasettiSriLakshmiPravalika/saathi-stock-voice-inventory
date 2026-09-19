"""
Dashboard API — aggregated data for frontend dashboard display.

All values come from real backend services.
No fake or mock dashboard values.
"""
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.user import User
from app.models.statement import Statement
from app.models.product import Product
from app.models.review import Review
from app.models.trust_history import TrustHistory
from app.models.enums import StatementStatus, DirectionEnum, ReviewStatus
from app.dependencies import get_current_user, get_shop_or_404, require_shop_member
from app.services.inventory_service import get_shop_inventory

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get("")
async def get_dashboard(
    shop_id: uuid.UUID = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get dashboard data for a shop."""
    await get_shop_or_404(shop_id, db)
    await require_shop_member(shop_id, current_user, db)

    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    # Total products
    prod_result = await db.execute(
        select(func.count(Product.id)).where(
            Product.shop_id == shop_id,
            Product.is_active == True,
        )
    )
    total_products = int(prod_result.scalar() or 0)

    # Inventory
    inventory = await get_shop_inventory(db, shop_id)

    # Today's sales (CONFIRMED OUT)
    sales_result = await db.execute(
        select(func.coalesce(func.sum(Statement.quantity), 0)).where(
            Statement.shop_id == shop_id,
            Statement.direction == DirectionEnum.OUT,
            Statement.status == StatementStatus.CONFIRMED,
            Statement.created_at >= today_start,
        )
    )
    sales_today = float(sales_result.scalar() or 0)

    # Today's incoming (CONFIRMED IN)
    in_result = await db.execute(
        select(func.coalesce(func.sum(Statement.quantity), 0)).where(
            Statement.shop_id == shop_id,
            Statement.direction == DirectionEnum.IN,
            Statement.status == StatementStatus.CONFIRMED,
            Statement.created_at >= today_start,
        )
    )
    incoming_today = float(in_result.scalar() or 0)

    # Pending reviews
    review_result = await db.execute(
        select(func.count(Review.id)).where(
            Review.shop_id == shop_id,
            Review.status == ReviewStatus.PENDING,
        )
    )
    pending_reviews = int(review_result.scalar() or 0)

    # Low stock products
    low_stock = [
        item for item in inventory
        if item.get("current_stock") is not None and
        (item["current_stock"] < 5 or
         (item.get("baseline_quantity") and item["baseline_quantity"] > 0
          and item["current_stock"] / item["baseline_quantity"] < 0.1))
    ]

    # Recent activity (last 10 statements)
    recent_result = await db.execute(
        select(Statement).where(
            Statement.shop_id == shop_id,
        ).order_by(Statement.created_at.desc()).limit(10)
    )
    recent_statements = recent_result.scalars().all()

    return {
        "success": True,
        "data": {
            "total_products": total_products,
            "inventory_summary": inventory,
            "sales_today": sales_today,
            "incoming_today": incoming_today,
            "pending_reviews": pending_reviews,
            "low_stock_count": len(low_stock),
            "low_stock_products": low_stock,
            "recent_activity": [
                {
                    "id": str(s.id),
                    "direction": s.direction.value if s.direction else None,
                    "quantity": float(s.quantity) if s.quantity else None,
                    "unit": s.unit,
                    "status": s.status.value,
                    "product_id": str(s.product_id) if s.product_id else None,
                    "transcript": s.transcript,
                    "created_at": s.created_at.isoformat(),
                }
                for s in recent_statements
            ],
        },
    }
