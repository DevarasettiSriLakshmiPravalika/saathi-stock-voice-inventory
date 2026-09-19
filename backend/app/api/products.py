"""
Products API — CRUD for shop products.
No current_stock column. Stock derived from baselines + confirmed statements.
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.models.product import Product
from app.models.audit_log import AuditLog
from app.models.enums import AuditAction
from app.schemas.product import ProductCreate, ProductUpdate
from app.dependencies import get_current_user, get_shop_or_404, require_shop_owner, require_shop_member

router = APIRouter(tags=["products"])


def _product_dict(p: Product) -> dict:
    return {
        "id": str(p.id),
        "shop_id": str(p.shop_id),
        "name": p.name,
        "default_unit": p.default_unit,
        "is_active": p.is_active,
        "created_at": p.created_at.isoformat(),
        "updated_at": p.updated_at.isoformat(),
    }


@router.post("/api/v1/shops/{shop_id}/products")
async def create_product(
    shop_id: uuid.UUID,
    body: ProductCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_shop_or_404(shop_id, db)
    await require_shop_owner(shop_id, current_user, db)

    # Check duplicate name in shop
    result = await db.execute(
        select(Product).where(Product.shop_id == shop_id, Product.name == body.name)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "VALIDATION_ERROR", "message": f"Product '{body.name}' already exists in this shop."},
        )

    product = Product(
        shop_id=shop_id,
        name=body.name,
        default_unit=body.default_unit,
        is_active=True,
    )
    db.add(product)
    await db.flush()

    audit = AuditLog(
        shop_id=shop_id,
        actor_id=current_user.id,
        action=AuditAction.PRODUCT_CREATED.value,
        entity_type="product",
        entity_id=product.id,
        metadata_={"name": body.name, "default_unit": body.default_unit},
    )
    db.add(audit)
    await db.commit()
    await db.refresh(product)

    return {"success": True, "data": _product_dict(product)}


@router.get("/api/v1/shops/{shop_id}/products")
async def list_products(
    shop_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_shop_or_404(shop_id, db)
    await require_shop_member(shop_id, current_user, db)

    result = await db.execute(
        select(Product).where(
            Product.shop_id == shop_id,
            Product.is_active == True,
        ).order_by(Product.name)
    )
    products = result.scalars().all()
    return {"success": True, "data": [_product_dict(p) for p in products]}


@router.put("/api/v1/products/{product_id}")
async def update_product(
    product_id: uuid.UUID,
    body: ProductUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Product not found."},
        )
    await require_shop_owner(product.shop_id, current_user, db)

    if body.name is not None:
        product.name = body.name
    if body.default_unit is not None:
        product.default_unit = body.default_unit
    if body.is_active is not None:
        product.is_active = body.is_active

    audit = AuditLog(
        shop_id=product.shop_id,
        actor_id=current_user.id,
        action=AuditAction.PRODUCT_UPDATED.value,
        entity_type="product",
        entity_id=product.id,
    )
    db.add(audit)
    await db.commit()
    await db.refresh(product)
    return {"success": True, "data": _product_dict(product)}


@router.delete("/api/v1/products/{product_id}")
async def deactivate_product(
    product_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Deactivate a product (soft delete — preserves audit trail)."""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Product not found."},
        )
    await require_shop_owner(product.shop_id, current_user, db)

    product.is_active = False
    audit = AuditLog(
        shop_id=product.shop_id,
        actor_id=current_user.id,
        action=AuditAction.PRODUCT_UPDATED.value,
        entity_type="product",
        entity_id=product.id,
        metadata_={"deactivated": True},
    )
    db.add(audit)
    await db.commit()
    return {"success": True, "data": {"id": str(product_id), "is_active": False}}
