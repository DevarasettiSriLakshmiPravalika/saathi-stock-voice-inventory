"""
Query API — owner natural-language inventory queries.

POST /api/v1/query

LLM parses intent. Deterministic DB queries provide the actual answer.
LLM never invents inventory numbers.
"""
import uuid
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.user import User
from app.models.statement import Statement
from app.models.product import Product
from app.models.review import Review
from app.models.enums import StatementStatus, DirectionEnum, ReviewStatus
from app.dependencies import get_current_user, require_shop_member
from app.providers.llm_provider import get_llm_provider
from app.services.inventory_service import calculate_stock, get_shop_inventory

router = APIRouter(prefix="/api/v1/query", tags=["query"])


class QueryRequest(BaseModel):
    shop_id: uuid.UUID
    query: str


@router.post("")
async def owner_query(
    body: QueryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Natural-language query endpoint.

    LLM interprets intent. Backend provides authoritative data from DB.
    LLM never invents inventory numbers.
    """
    await require_shop_member(body.shop_id, current_user, db)

    llm = get_llm_provider()
    intent = await llm.parse_query_intent(body.query)

    result_data = {}
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    if intent.intent == "CURRENT_STOCK":
        if intent.product_name:
            # Find product by name
            prod_result = await db.execute(
                select(Product).where(
                    Product.shop_id == body.shop_id,
                    Product.name.ilike(f"%{intent.product_name}%"),
                    Product.is_active == True,
                ).limit(1)
            )
            product = prod_result.scalar_one_or_none()
            if product:
                stock = await calculate_stock(db, body.shop_id, product.id)
                result_data = {"product": product.name, **stock}
            else:
                result_data = {"message": f"Product '{intent.product_name}' not found."}
        else:
            # All products
            result_data = {"inventory": await get_shop_inventory(db, body.shop_id)}

    elif intent.intent == "SALES_TODAY":
        # CONFIRMED OUT statements today
        result = await db.execute(
            select(
                Product.name,
                func.sum(Statement.quantity).label("total"),
                Statement.unit,
            ).join(Product, Statement.product_id == Product.id).where(
                Statement.shop_id == body.shop_id,
                Statement.direction == DirectionEnum.OUT,
                Statement.status == StatementStatus.CONFIRMED,
                Statement.created_at >= today_start,
            ).group_by(Product.name, Statement.unit)
        )
        rows = result.all()
        result_data = {
            "sales_today": [
                {"product": r.name, "quantity": float(r.total or 0), "unit": r.unit}
                for r in rows
            ]
        }

    elif intent.intent == "RECEIPTS_TODAY":
        # CONFIRMED IN statements today
        result = await db.execute(
            select(
                Product.name,
                func.sum(Statement.quantity).label("total"),
                Statement.unit,
            ).join(Product, Statement.product_id == Product.id).where(
                Statement.shop_id == body.shop_id,
                Statement.direction == DirectionEnum.IN,
                Statement.status == StatementStatus.CONFIRMED,
                Statement.created_at >= today_start,
            ).group_by(Product.name, Statement.unit)
        )
        rows = result.all()
        result_data = {
            "receipts_today": [
                {"product": r.name, "quantity": float(r.total or 0), "unit": r.unit}
                for r in rows
            ]
        }

    elif intent.intent == "LOW_STOCK":
        inventory = await get_shop_inventory(db, body.shop_id)
        # Low stock: less than 10% of baseline or < 5 units
        low = [
            item for item in inventory
            if item.get("current_stock") is not None and
            (item["current_stock"] < 5 or
             (item.get("baseline_quantity") and item["baseline_quantity"] > 0
              and item["current_stock"] / item["baseline_quantity"] < 0.1))
        ]
        result_data = {"low_stock_products": low}

    elif intent.intent == "REVIEW_QUEUE":
        result = await db.execute(
            select(Review).where(
                Review.shop_id == body.shop_id,
                Review.status == ReviewStatus.PENDING,
            ).order_by(Review.created_at.desc()).limit(20)
        )
        reviews = result.scalars().all()
        result_data = {
            "pending_reviews": len(reviews),
            "reviews": [{"id": str(r.id), "statement_id": str(r.statement_id), "created_at": r.created_at.isoformat()} for r in reviews],
        }

    elif intent.intent == "PRODUCT_HISTORY":
        if intent.product_name:
            prod_result = await db.execute(
                select(Product).where(
                    Product.shop_id == body.shop_id,
                    Product.name.ilike(f"%{intent.product_name}%"),
                ).limit(1)
            )
            product = prod_result.scalar_one_or_none()
            if product:
                hist_result = await db.execute(
                    select(Statement).where(
                        Statement.product_id == product.id,
                        Statement.status == StatementStatus.CONFIRMED,
                    ).order_by(Statement.created_at.desc()).limit(20)
                )
                statements = hist_result.scalars().all()
                result_data = {
                    "product": product.name,
                    "history": [
                        {
                            "direction": s.direction.value if s.direction else None,
                            "quantity": float(s.quantity) if s.quantity else None,
                            "unit": s.unit,
                            "created_at": s.created_at.isoformat(),
                        }
                        for s in statements
                    ],
                }
            else:
                result_data = {"message": f"Product '{intent.product_name}' not found."}
        else:
            result_data = {"message": "Specify a product name for history."}

    elif intent.intent == "STATEMENT_SEARCH":
        result = await db.execute(
            select(Statement).where(
                Statement.shop_id == body.shop_id,
            ).order_by(Statement.created_at.desc()).limit(10)
        )
        statements = result.scalars().all()
        result_data = {
            "recent_statements": [
                {
                    "id": str(s.id),
                    "transcript": s.transcript,
                    "actor_id": str(s.actor_id) if s.actor_id else None,
                    "direction": s.direction.value if s.direction else None,
                    "quantity": float(s.quantity) if s.quantity else None,
                    "status": s.status.value,
                    "created_at": s.created_at.isoformat(),
                }
                for s in statements
            ]
        }

    else:
        # Default: return current inventory
        result_data = {"inventory": await get_shop_inventory(db, body.shop_id)}

    return {
        "success": True,
        "data": {
            "query": body.query,
            "intent": intent.intent,
            "product_name": intent.product_name,
            "result": result_data,
        },
    }
