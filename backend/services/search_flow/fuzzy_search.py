from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models.product import Product
from db.models.product_attribute import ProductAttribute


FUZZY_THRESHOLD = 0.25


async def fuzzy_search(session: AsyncSession, query: str, limit: int = 20):
    if not query or not query.strip():
        return []

    searchable_name = func.coalesce(
        Product.normalized_name,
        Product.name,
    )

    similarity_score = func.similarity(
        searchable_name,
        query.strip(),
    )

    stmt = (
        select(
            Product,
            similarity_score.label("similarity"),
        )
        .options(
            selectinload(Product.product_attributes).selectinload(
                ProductAttribute.attribute
            )
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
