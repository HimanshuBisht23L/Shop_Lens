"""
Unit tests for search flow components (embedding generator, dimension, caching).
These run completely in memory without requiring database connection.
"""

from services.search_flow.semantic_search import (
    MODEL_NAME,
    BASE_MODEL_NAME,
    FINE_TUNED_MODEL_PATH,
    get_embedding_model,
    generate_query_embedding,
)


def test_embedding_model_name():
    assert MODEL_NAME in [BASE_MODEL_NAME, str(FINE_TUNED_MODEL_PATH)]


def test_embedding_model_is_cached():
    model1 = get_embedding_model()
    model2 = get_embedding_model()
    assert model1 is model2


def test_query_embedding_dimension():
    vec = generate_query_embedding("test query")
    assert isinstance(vec, list)
    assert len(vec) == 384
    # All elements must be floats
    assert all(isinstance(x, float) for x in vec)


def test_query_embedding_is_normalized():
    # Since normalize_embeddings=True, L2 norm should be approximately 1.0
    vec = generate_query_embedding("chocolate")
    l2_norm = sum(x * x for x in vec) ** 0.5
    assert abs(l2_norm - 1.0) < 1e-4
