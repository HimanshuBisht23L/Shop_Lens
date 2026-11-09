"""
Full-Text Search (BM25-style) Module for ShopLens Search V2.

Leverages PostgreSQL native Full-Text Search (tsvector and tsquery):
1. Matches query tokens against weighted search_vector (Title: Weight A, Brand: Weight A, Sub_category/Tags: Weight B, Description: Weight C).
2. Calculates cover density relevance score using ts_rank_cd.
3. Falls back to prefix matching (token:*) for partial keywords.
4. Supports Type A entity gating (sub-category and brand bounds).
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models.product import Product


async def full_text_search(
    session: AsyncSession,
    query: str,
    limit: int = 60,
    allowed_sub_category: str | None = None,
    allowed_brand: str | None = None,
    allowed_category_ids: list[int] | None = None,
    allowed_sub_category_ids: list[int] | None = None,
) -> list[tuple[Product, float]]:
    clean_q = query.strip()
    if not clean_q:
        return []

    # 1. Primary search: plainto_tsquery
    tsquery_expr = func.plainto_tsquery("english", clean_q)
    rank_expr = func.ts_rank_cd(Product.search_vector, tsquery_expr).label("fts_rank")

    stmt = (
        select(Product, rank_expr)
        .options(
            selectinload(Product.category),
            selectinload(Product.sub_category),
        )
        .where(
            Product.is_active == True,
            Product.search_vector.op("@@")(tsquery_expr),
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

    stmt = stmt.order_by(rank_expr.desc()).limit(limit)

    result = await session.execute(stmt)
    rows = result.all()

    # 2. If no exact lexemes matched, attempt prefix matching on alphanumeric tokens
    if not rows:
        tokens = [t for t in clean_q.split() if t.isalnum()]
        if tokens:
            prefix_query_str = " & ".join(f"{t}:*" for t in tokens)
            prefix_tsquery = func.to_tsquery("english", prefix_query_str)
            prefix_rank = func.ts_rank_cd(Product.search_vector, prefix_tsquery).label("fts_rank")

            prefix_stmt = (
                select(Product, prefix_rank)
                .options(
                    selectinload(Product.category),
                    selectinload(Product.sub_category),
                )
                .where(
                    Product.is_active == True,
                    Product.search_vector.op("@@")(prefix_tsquery),
                )
            )

            if allowed_sub_category_ids:
                prefix_stmt = prefix_stmt.where(Product.sub_category_id.in_(allowed_sub_category_ids))
            elif allowed_category_ids:
                prefix_stmt = prefix_stmt.where(Product.category_id.in_(allowed_category_ids))
            if allowed_sub_category:
                prefix_stmt = prefix_stmt.where(Product.sub_category_name == allowed_sub_category)
            if allowed_brand:
                prefix_stmt = prefix_stmt.where(Product.brand == allowed_brand)

            prefix_stmt = prefix_stmt.order_by(prefix_rank.desc()).limit(limit)
            prefix_result = await session.execute(prefix_stmt)
            rows = prefix_result.all()

    return [(row[0], float(row[1])) for row in rows]
