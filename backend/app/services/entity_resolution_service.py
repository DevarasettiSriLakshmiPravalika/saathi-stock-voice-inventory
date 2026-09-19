"""
Entity resolution service — maps spoken terms to shop products.

Resolution order:
1. Exact match (case-insensitive)
2. Normalized match (strip whitespace, lowercase)
3. Shop vocabulary aliases
4. Controlled fuzzy matching (edit distance)

Ambiguous results REQUIRE review — never silently map wrong products.
"""
import uuid
from difflib import SequenceMatcher
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.product import Product
from app.models.vocabulary_entry import VocabularyEntry
from app.models.enums import VocabularyMappingType

FUZZY_THRESHOLD = 0.8  # Minimum similarity ratio for fuzzy match


class EntityResolutionResult:
    def __init__(
        self,
        product: Optional[Product],
        match_type: str,  # EXACT | NORMALIZED | VOCAB_ALIAS | FUZZY | NOT_FOUND | AMBIGUOUS
        confidence: float,
        matched_term: str,
    ):
        self.product = product
        self.match_type = match_type
        self.confidence = confidence
        self.matched_term = matched_term

    @property
    def resolved(self) -> bool:
        return self.product is not None and self.match_type != "AMBIGUOUS"


async def resolve_product(
    db: AsyncSession,
    shop_id: uuid.UUID,
    product_term: str,
) -> EntityResolutionResult:
    """
    Resolve a product term to a shop product.
    Never silently maps ambiguous products.
    """
    if not product_term or not product_term.strip():
        return EntityResolutionResult(None, "NOT_FOUND", 0.0, product_term)

    term = product_term.strip()
    term_lower = term.lower()

    # Get all active products for this shop
    result = await db.execute(
        select(Product).where(Product.shop_id == shop_id, Product.is_active == True)
    )
    products = result.scalars().all()

    if not products:
        return EntityResolutionResult(None, "NOT_FOUND", 0.0, term)

    # 1. Exact match (case-insensitive)
    for p in products:
        if p.name.lower() == term_lower:
            return EntityResolutionResult(p, "EXACT", 1.0, term)

    # 2. Normalized match (remove extra spaces, common variations)
    norm_term = " ".join(term_lower.split())
    for p in products:
        if " ".join(p.name.lower().split()) == norm_term:
            return EntityResolutionResult(p, "NORMALIZED", 0.98, term)

    # 3. Shop vocabulary aliases
    vocab_result = await db.execute(
        select(VocabularyEntry).where(
            VocabularyEntry.shop_id == shop_id,
            VocabularyEntry.mapping_type == VocabularyMappingType.PRODUCT_ALIAS,
            VocabularyEntry.is_active == True,
        )
    )
    vocab_entries = vocab_result.scalars().all()

    for entry in vocab_entries:
        if entry.source_term.lower() == term_lower and entry.target_product_id:
            # Find the target product
            for p in products:
                if p.id == entry.target_product_id:
                    return EntityResolutionResult(p, "VOCAB_ALIAS", 0.95, term)

    # 4. Fuzzy matching — controlled similarity
    best_ratio = 0.0
    best_products = []

    for p in products:
        ratio = SequenceMatcher(None, term_lower, p.name.lower()).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_products = [p]
        elif ratio == best_ratio and ratio >= FUZZY_THRESHOLD:
            best_products.append(p)

    if best_ratio >= FUZZY_THRESHOLD:
        if len(best_products) == 1:
            return EntityResolutionResult(best_products[0], "FUZZY", best_ratio, term)
        else:
            # Ambiguous — multiple products with same similarity
            return EntityResolutionResult(None, "AMBIGUOUS", best_ratio, term)

    return EntityResolutionResult(None, "NOT_FOUND", 0.0, term)


async def resolve_unit(
    db: AsyncSession,
    shop_id: uuid.UUID,
    unit_term: str,
) -> Optional[str]:
    """
    Resolve a unit term via vocabulary. Returns canonical unit or None.
    """
    term_lower = unit_term.lower().strip()

    vocab_result = await db.execute(
        select(VocabularyEntry).where(
            VocabularyEntry.shop_id == shop_id,
            VocabularyEntry.mapping_type.in_([
                VocabularyMappingType.UNIT_ALIAS,
                VocabularyMappingType.UNIT_CONVERSION,
            ]),
            VocabularyEntry.is_active == True,
        )
    )
    entries = vocab_result.scalars().all()

    for entry in entries:
        if entry.source_term.lower() == term_lower and entry.target_unit:
            return entry.target_unit

    # Return as-is if no mapping found
    return unit_term
