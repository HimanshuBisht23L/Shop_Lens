"""
Pytest configuration and shared fixtures for ShopLens test suite.
"""

import sys
import os
from pathlib import Path

# Set offline mode for sentence-transformers/huggingface
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

# Ensure backend directory is in sys.path
TESTS_DIR = Path(__file__).resolve().parent
BACKEND_DIR = TESTS_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from config import settings
from db.database import get_db
from main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def db_session():
    """
    Provides a per-test isolated AsyncSession using NullPool to avoid event-loop connection sharing issues.
    """
    engine = create_async_engine(
        settings.DATABASE_URL,
        poolclass=NullPool,
        echo=False,
    )
    session_maker = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_maker() as session:
        yield session
    await engine.dispose()


@pytest.fixture
async def async_client(db_session: AsyncSession):
    """
    Provides an HTTPX AsyncClient with the FastAPI test application and overridden DB dependency.
    """
    import httpx

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
