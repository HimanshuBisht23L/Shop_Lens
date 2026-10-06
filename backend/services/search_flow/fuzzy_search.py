from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.product import Product


FUZZY_THRESHOLD = 0.25


async def fuzzy_search(session: AsyncSession, query: str, limit: int = 20) :
    
    searchable_name = func.coalesce(
        Product.normalized_name,
        Product.name,
    )

    similarity_score = func.similarity(
        searchable_name,
        query,
    )

    stmt = (
        select(
            Product,
            similarity_score.label("similarity"),
        )
        .where(
            similarity_score >= FUZZY_THRESHOLD
        )
        .order_by(
            similarity_score.desc()
        )
        .limit(limit)
    )

    result = await session.execute(stmt)

    return result.all()