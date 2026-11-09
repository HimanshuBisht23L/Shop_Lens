"""
Fuzzy Trigram Search Module for ShopLens Search V2.

Leverages PostgreSQL pg_trgm word_similarity:
- Matches typos against individual words within the product title (e.g. 'choclate' inside 'Cadbury Dairy Milk Chocholate').
- Eliminates the penalty long titles suffered under global similarity.
- Supports Type A entity gating (sub-category and brand bounds).
- Threshold default: 0.30.
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models.product import Product

FUZZY_WORD_THRESHOLD = 0.30


async def fuzzy_search(
    session: AsyncSession,
    query: str,
    limit: int = 60,
    threshold: float = FUZZY_WORD_THRESHOLD,
    allowed_sub_category: str | None = None,
    allowed_brand: str | None = None,
    allowed_category_ids: list[int] | None = None,
    allowed_sub_category_ids: list[int] | None = None,
) -> list[tuple[Product, float]]:
    clean_q = query.strip()
    if not clean_q:
        return []

    # word_similarity(needle, haystack): how well query matches any word window in product name
    wsim_score = func.word_similarity(clean_q, Product.name).label("word_similarity")

    stmt = (
        select(Product, wsim_score)
        .options(
            selectinload(Product.category),
            selectinload(Product.sub_category),
        )
        .where(
            Product.is_active == True,
            func.word_similarity(clean_q, Product.name) >= threshold,
        )
    )

    if allowed_sub_category_ids:
        stmt = stmt.where(Product.sub_category_id.in_(allowed_sub_category_ids))
    elif allowed_category_ids:
        stmt = stmt.where(Product.category_id.in_(allowed_category_ids))

    if allowed_sub_category:
        stmt = stmt.where(Product.sub_category_name == allowed_sub_category)
    if allowed_brand:
        stmt = stmt.where(Product.brand == allowed_brand)

    stmt = stmt.order_by(wsim_score.desc()).limit(limit)

    result = await session.execute(stmt)
    rows = result.all()
    return [(row[0], float(row[1])) for row in rows]
