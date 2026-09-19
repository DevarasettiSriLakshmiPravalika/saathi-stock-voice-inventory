"""
Members API — manage shop members (OWNER/STAFF/OUTSIDER).
"""
import uuid
import re
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.models.shop_member import ShopMember
from app.models.audit_log import AuditLog
from app.models.enums import UserRole, MembershipStatus, AuditAction
from app.schemas.shop_member import ShopMemberCreate, ShopMemberUpdate
from app.dependencies import get_current_user, get_shop_or_404, require_shop_owner
from app.services import auth_service

router = APIRouter(tags=["members"])


def _member_dict(m: ShopMember) -> dict:
    return {
        "id": str(m.id),
        "shop_id": str(m.shop_id),
        "user_id": str(m.user_id),
        "role": m.role.value,
        "status": m.status.value,
        "created_at": m.created_at.isoformat(),
        "updated_at": m.updated_at.isoformat(),
    }


@router.post("/api/v1/shops/{shop_id}/members")
async def add_member(
    shop_id: uuid.UUID,
    body: ShopMemberCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_shop_or_404(shop_id, db)
    await require_shop_owner(shop_id, current_user, db)

    # Look up or create user by phone
    if not re.match(r"^\+[1-9]\d{6,14}$", body.phone):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "VALIDATION_ERROR", "message": "Phone must be in E.164 format."},
        )

    user = await auth_service.get_user_by_phone(db, body.phone)
    if not user:
        user = await auth_service.create_user(db, body.name, body.phone)
        await db.flush()

    # Check if already a member
    result = await db.execute(
        select(ShopMember).where(
            ShopMember.shop_id == shop_id,
            ShopMember.user_id == user.id,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        if existing.status == MembershipStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "VALIDATION_ERROR", "message": "User is already a member of this shop."},
            )
        # Reactivate
        existing.role = body.role
        existing.status = MembershipStatus.ACTIVE
        await db.commit()
        await db.refresh(existing)
        return {"success": True, "data": _member_dict(existing)}

    member = ShopMember(
        shop_id=shop_id,
        user_id=user.id,
        role=body.role,
        status=MembershipStatus.ACTIVE,
    )
    db.add(member)
    await db.flush()

    audit = AuditLog(
        shop_id=shop_id,
        actor_id=current_user.id,
        action=AuditAction.MEMBER_ADDED.value,
        entity_type="shop_member",
        entity_id=member.id,
        metadata_={"role": body.role.value, "user_id": str(user.id)},
    )
    db.add(audit)
    await db.commit()
    await db.refresh(member)

    return {"success": True, "data": _member_dict(member)}


@router.get("/api/v1/shops/{shop_id}/members")
async def list_members(
    shop_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_shop_or_404(shop_id, db)
    await require_shop_owner(shop_id, current_user, db)

    result = await db.execute(
        select(ShopMember).where(ShopMember.shop_id == shop_id)
    )
    members = result.scalars().all()
    return {"success": True, "data": [_member_dict(m) for m in members]}


@router.put("/api/v1/members/{member_id}")
async def update_member(
    member_id: uuid.UUID,
    body: ShopMemberUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ShopMember).where(ShopMember.id == member_id))
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Member not found."},
        )
    await require_shop_owner(member.shop_id, current_user, db)

    if body.role is not None:
        member.role = body.role
    if body.status is not None:
        member.status = body.status

    audit = AuditLog(
        shop_id=member.shop_id,
        actor_id=current_user.id,
        action=AuditAction.MEMBER_UPDATED.value,
        entity_type="shop_member",
        entity_id=member.id,
    )
    db.add(audit)
    await db.commit()
    await db.refresh(member)
    return {"success": True, "data": _member_dict(member)}


@router.delete("/api/v1/members/{member_id}")
async def deactivate_member(
    member_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ShopMember).where(ShopMember.id == member_id))
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Member not found."},
        )
    await require_shop_owner(member.shop_id, current_user, db)

    member.status = MembershipStatus.INACTIVE
    audit = AuditLog(
        shop_id=member.shop_id,
        actor_id=current_user.id,
        action=AuditAction.MEMBER_UPDATED.value,
        entity_type="shop_member",
        entity_id=member.id,
        metadata_={"deactivated": True},
    )
    db.add(audit)
    await db.commit()
    return {"success": True, "data": {"id": str(member_id), "status": "INACTIVE"}}
