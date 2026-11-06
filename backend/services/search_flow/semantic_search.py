import asyncio
from functools import lru_cache
from pathlib import Path

from sentence_transformers import SentenceTransformer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models.product import Product
from db.models.product_attribute import ProductAttribute


BASE_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
FINE_TUNED_MODEL_PATH = BACKEND_DIR / "ml" / "semantic_search" / "models" / "best_model"

# Load the fine-tuned checkpoint if available; fallback to base pretrained model
if not (
    FINE_TUNED_MODEL_PATH.exists()
    and (FINE_TUNED_MODEL_PATH / "config.json").exists()
):
    raise FileNotFoundError(
        f"Fine-tuned semantic model not found: {FINE_TUNED_MODEL_PATH}"
    )

MODEL_NAME = str(FINE_TUNED_MODEL_PATH)

# Note: Raw cosine similarity is not a probability. Threshold filtering
# is handled during candidate ranking rather than hard SQL cutoff.
SEMANTIC_THRESHOLD = 0.35


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """
    Load the Sentence Transformer model only once
    per application process.
    """

    print(f"Loading Sentence Transformer model: {MODEL_NAME}")
    return SentenceTransformer(MODEL_NAME)


def generate_query_embedding(query: str) -> list[float]:
    """
    Convert the search query into a 384-dimensional normalized embedding.
    """
    model = get_embedding_model()

    embedding = model.encode(
        query,
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    return embedding.tolist()


async def semantic_search(session: AsyncSession, query: str, limit: int = 20):
    """
    Find semantically similar products using pgvector cosine distance.
    Inference runs in a worker threadpool so the asyncio event loop is not blocked.
    """
    if not query or not query.strip():
        return []

    # Run CPU-bound embedding generation in threadpool
    query_embedding = await asyncio.to_thread(
        generate_query_embedding,
        query.strip(),
    )

    # Calculate cosine distance
    distance = Product.embedding.cosine_distance(query_embedding)

    # Convert distance into similarity: 1 - cosine_distance
    similarity_score = (1 - distance).label("similarity")

    # Semantic search query
    stmt = (
        select(
            Product,
            similarity_score,
        )
        .options(
            selectinload(Product.product_attributes).selectinload(
                ProductAttribute.attribute
            )
        )
        .where(
            Product.embedding.is_not(None)
        )
        .order_by(
            distance.asc()
        )
        .limit(limit)
    )

    result = await session.execute(stmt)

    return result.all()
