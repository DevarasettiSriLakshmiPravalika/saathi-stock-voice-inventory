"""
Vocabulary API — shop-specific term mappings.
"""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.models.vocabulary_entry import VocabularyEntry
from app.schemas.vocabulary_entry import VocabularyEntryCreate
from app.dependencies import get_current_user, get_shop_or_404, require_shop_owner, require_shop_member

router = APIRouter(prefix="/api/v1/vocabulary", tags=["vocabulary"])


def _vocab_dict(v: VocabularyEntry) -> dict:
    return {
        "id": str(v.id),
        "shop_id": str(v.shop_id),
        "source_term": v.source_term,
        "mapping_type": v.mapping_type.value,
        "target_product_id": str(v.target_product_id) if v.target_product_id else None,
        "target_unit": v.target_unit,
        "conversion_factor": float(v.conversion_factor) if v.conversion_factor else None,
        "is_active": v.is_active,
        "created_at": v.created_at.isoformat(),
        "updated_at": v.updated_at.isoformat(),
    }


@router.post("")
async def create_vocabulary_entry(
    body: VocabularyEntryCreate,
    shop_id: uuid.UUID = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a shop vocabulary entry. OWNER only."""
    await get_shop_or_404(shop_id, db)
    await require_shop_owner(shop_id, current_user, db)

    # Check duplicate
    result = await db.execute(
        select(VocabularyEntry).where(
            VocabularyEntry.shop_id == shop_id,
            VocabularyEntry.source_term == body.source_term,
            VocabularyEntry.mapping_type == body.mapping_type,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        existing.target_product_id = body.target_product_id
        existing.target_unit = body.target_unit
        existing.conversion_factor = body.conversion_factor
        existing.is_active = True
        await db.commit()
        await db.refresh(existing)
        return {"success": True, "data": _vocab_dict(existing)}

    entry = VocabularyEntry(
        shop_id=shop_id,
        source_term=body.source_term,
        mapping_type=body.mapping_type,
        target_product_id=body.target_product_id,
        target_unit=body.target_unit,
        conversion_factor=body.conversion_factor,
        is_active=True,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)

    return {"success": True, "data": _vocab_dict(entry)}


@router.delete("/{entry_id}")
async def delete_vocabulary_entry(
    entry_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a vocabulary entry. OWNER only."""
    result = await db.execute(select(VocabularyEntry).where(VocabularyEntry.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Vocabulary entry not found."})
    await require_shop_owner(entry.shop_id, current_user, db)
    await db.delete(entry)
    await db.commit()
    return {"success": True, "data": {"id": str(entry_id), "deleted": True}}


@router.get("")
async def list_vocabulary(
    shop_id: uuid.UUID = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all vocabulary entries for a shop."""
    await get_shop_or_404(shop_id, db)
    await require_shop_member(shop_id, current_user, db)

    result = await db.execute(
        select(VocabularyEntry).where(
            VocabularyEntry.shop_id == shop_id,
        ).order_by(VocabularyEntry.source_term)
    )
    entries = result.scalars().all()
    return {"success": True, "data": [_vocab_dict(e) for e in entries]}
