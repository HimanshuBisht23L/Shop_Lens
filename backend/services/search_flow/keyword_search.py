from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models.product import Product
from db.models.product_attribute import ProductAttribute


async def keyword_search(session: AsyncSession, query: str, limit: int = 20) -> list[Product]:
    if not query or not query.strip():
        return []

    stmt = (
        select(Product)
        .options(
            selectinload(Product.product_attributes).selectinload(
                ProductAttribute.attribute
            )
        )
        .where(
            Product.name.ilike(f"%{query.strip()}%")
        )
        .limit(limit)
    )

    result = await session.execute(stmt)

    return list(result.scalars().all())
