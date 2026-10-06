from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.models.product import Product

# import asyncio
# from db.database import AsyncSessionLocal



async def keyword_search(session: AsyncSession, query: str, limit: int = 20) -> list[Product] :

    stmt = (
        select(Product)
        .where(
            Product.name.ilike(f"%{query}%")
        )
        .limit(limit)
    )

    result = await session.execute(stmt)

    return list(result.scalars().all())



# async def test():
#     async with AsyncSessionLocal() as session:

#         results = await keyword_search(
#             session=session,
#             query="chocolate"
#         )

#         for product in results:
#             print(product.id, product.name)


# if __name__ == "__main__":
#     asyncio.run(test())