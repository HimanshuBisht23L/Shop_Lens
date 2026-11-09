"""
Dense Vector / Semantic Search Module for ShopLens Search V2.

Leverages BAAI/bge-small-en-v1.5 and PostgreSQL pgvector:
- Encodes queries into 384-dimensional normalized dense vectors with BGE retrieval instructions.
- Enforces strict gating for Type A queries (sub-category/brand restrictions).
- Enforces cosine similarity floor for Type B conceptual queries.
- Runs inference in an asyncio worker threadpool to avoid event loop blocking.
"""

import asyncio
from functools import lru_cache
import os
from pathlib import Path

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from sentence_transformers import SentenceTransformer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from config import settings
from core.logging import logger
from db.models.product import Product


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    model_path = Path(settings.EMBEDDING_MODEL_PATH)
    if not model_path.exists() or not (model_path / "config.json").exists():
        raise FileNotFoundError(f"Search V2 embedding model not found at {model_path}")
    logger.info(f"Loading Search V2 BGE SentenceTransformer model from {model_path}")
    return SentenceTransformer(str(model_path))


def encode_query(query: str) -> list[float]:
    model = get_embedding_model()
    # BGE query instruction for retrieval
    instruction = "Represent this sentence for searching relevant passages: "
    text_to_encode = f"{instruction}{query.strip()}"
    embedding = model.encode(
        text_to_encode,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return embedding.tolist()


async def vector_search(
    session: AsyncSession,
    query: str,
    limit: int = 60,
    min_similarity: float = 0.50,
    allowed_sub_category: str | None = None,
    allowed_brand: str | None = None,
    allowed_category_ids: list[int] | None = None,
    allowed_sub_category_ids: list[int] | None = None,
) -> list[tuple[Product, float]]:
    clean_q = query.strip()
    if not clean_q:
        return []

    # Encode query in worker threadpool to keep event loop responsive
    query_vector = await asyncio.to_thread(encode_query, clean_q)

    # Cosine distance operator (<=>)
    cosine_dist = Product.embedding.cosine_distance(query_vector)
    similarity = (1 - cosine_dist).label("similarity")

    stmt = (
        select(Product, similarity)
        .options(
            selectinload(Product.category),
            selectinload(Product.sub_category),
        )
        .where(
            Product.embedding.is_not(None),
            Product.is_active == True,
            similarity >= min_similarity,
        )
    )

    # Dynamic Taxonomy Scoping (Q2C) - Prefer granular sub-categories
    if allowed_sub_category_ids:
        stmt = stmt.where(Product.sub_category_id.in_(allowed_sub_category_ids))
    elif allowed_category_ids:
        stmt = stmt.where(Product.category_id.in_(allowed_category_ids))

    # Hard entity gate for Type A queries
    if allowed_sub_category:
        stmt = stmt.where(Product.sub_category_name == allowed_sub_category)
    if allowed_brand:
        stmt = stmt.where(Product.brand == allowed_brand)

    stmt = stmt.order_by(cosine_dist.asc()).limit(limit)

    result = await session.execute(stmt)
    rows = result.all()
    return [(row[0], float(row[1])) for row in rows]
