from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from config import settings


# ============================================================
# DATABASE ENGINE
# ============================================================

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,
)


# ============================================================
# SESSION FACTORY
# ============================================================

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ============================================================
# DECLARATIVE BASE
# ============================================================

class Base(DeclarativeBase):
    pass


# ============================================================
# FASTAPI DEPENDENCY
# ============================================================

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
