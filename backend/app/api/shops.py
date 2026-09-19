"""
Shops API — create, retrieve, update.
Only OWNER can manage shop configuration.
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.models.shop import Shop
from app.models.shop_member import ShopMember
from app.models.audit_log import AuditLog
from app.models.enums import UserRole, MembershipStatus, AuditAction
from app.schemas.shop import ShopCreate, ShopUpdate
from app.dependencies import get_current_user, get_shop_or_404, require_shop_owner

router = APIRouter(prefix="/api/v1/shops", tags=["shops"])


def _shop_dict(shop: Shop) -> dict:
    return {
        "id": str(shop.id),
        "name": shop.name,
        "owner_id": str(shop.owner_id),
        "is_active": shop.is_active,
        "created_at": shop.created_at.isoformat(),
        "updated_at": shop.updated_at.isoformat(),
    }


@router.get("")
async def list_user_shops(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all active shops the authenticated user belongs to."""
    result = await db.execute(
        select(Shop, ShopMember.role)
        .join(ShopMember, Shop.id == ShopMember.shop_id)
        .where(
            ShopMember.user_id == current_user.id,
            ShopMember.status == MembershipStatus.ACTIVE,
            Shop.is_active == True,
        )
        .order_by(Shop.name)
    )
    rows = result.all()
    shops_data = []
    for shop, role in rows:
        d = _shop_dict(shop)
        d["role"] = role.value
        shops_data.append(d)
    return {"success": True, "data": shops_data}


@router.post("")
async def create_shop(
    body: ShopCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new shop. Authenticated user becomes OWNER."""
    shop = Shop(name=body.name, owner_id=current_user.id, is_active=True)
    db.add(shop)
    await db.flush()

    # Add owner as shop member with OWNER role
    member = ShopMember(
        shop_id=shop.id,
        user_id=current_user.id,
        role=UserRole.OWNER,
        status=MembershipStatus.ACTIVE,
    )
    db.add(member)

    # Audit
    audit = AuditLog(
        shop_id=shop.id,
        actor_id=current_user.id,
        action=AuditAction.OWNER_CREATED_SHOP.value,
        entity_type="shop",
        entity_id=shop.id,
    )
    db.add(audit)

    await db.commit()
    await db.refresh(shop)

    return {"success": True, "data": _shop_dict(shop)}


@router.get("/{shop_id}")
async def get_shop(
    shop_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    shop = await get_shop_or_404(shop_id, db)
    # Must be a member
    result = await db.execute(
        select(ShopMember).where(
            ShopMember.shop_id == shop_id,
            ShopMember.user_id == current_user.id,
            ShopMember.status == MembershipStatus.ACTIVE,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "Not a member of this shop."},
        )
    return {"success": True, "data": _shop_dict(shop)}


@router.put("/{shop_id}")
async def update_shop(
    shop_id: uuid.UUID,
    body: ShopUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    shop = await get_shop_or_404(shop_id, db)
    await require_shop_owner(shop_id, current_user, db)

    if body.name is not None:
        shop.name = body.name
    if body.is_active is not None:
        shop.is_active = body.is_active

    await db.commit()
    await db.refresh(shop)
    return {"success": True, "data": _shop_dict(shop)}
