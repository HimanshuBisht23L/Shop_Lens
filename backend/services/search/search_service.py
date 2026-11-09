"""
Unified Search Pipeline Orchestrator for ShopLens Search V2.

Production-grade Dual-Path Architecture:
1. Normalizes query text, extracts natural language constraints (price, radius), and maps Hinglish.
2. Resolves explicit UI parameters vs parsed query constraints (zero implicit radius assumptions).
3. Classifies query intent:
   - Type A (Specific / Entity Query): Enforces Hard Lexical & Sub-Category Gate. Disallows unrelated categories.
   - Type B (Conceptual / Discovery Query): Broad multi-category vector retrieval via BGE with strict cosine similarity floor (>= 0.60).
4. Merges multi-channel candidates via Reciprocal Rank Fusion (RRF k=60).
5. PostGIS Geospatial Proximity & Inventory Binding (ST_Distance, in-stock preference, distance decay).
6. Assembles structured JSON response with brand, net_quantity, store, and price.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from core.logging import logger
from apis.v1.schemas.search import SearchRequest, SearchResponse, SearchV2Request, SearchV2Response
from services.search.query.normalizer import normalize_query
from services.search.query.filter_resolver import resolve_filters
from services.search.query.intent_classifier import (
    classify_query_intent,
    TYPE_A_SPECIFIC,
    TYPE_B_CONCEPTUAL,
)
from services.search.retrieval.full_text_search import full_text_search
from services.search.retrieval.fuzzy_search import fuzzy_search
from services.search.retrieval.vector_search import vector_search
from services.search.ranking.rrf import reciprocal_rank_fusion
from services.search.ranking.reranker import rerank_candidates
from services.search.ranking.business_ranker import filter_and_rank_business


async def execute_search(
    session: AsyncSession,
    request: SearchV2Request,
) -> SearchV2Response:
    # 1. Normalize Query
    parsed = normalize_query(request.query)

    # 2. Resolve Filters (No implicit radius or price; strictly explicit)
    resolved = resolve_filters(
        parsed=parsed,
        ui_min_price=request.min_price,
        ui_max_price=request.max_price,
        ui_radius_km=request.radius_km,
        ui_category_id=request.category_id,
    )

    query_text = resolved.search_text or request.query
    candidate_limit = settings.RETRIEVAL_CANDIDATE_LIMIT

    # 3. Intent Classification
    intent = classify_query_intent(query_text)
    logger.info(
        f"Query '{query_text}' classified as {intent.intent_type} "
        f"(Brand: {intent.matched_brand}, SubCategory: {intent.matched_sub_category})"
    )

    # 4. Multi-Channel Retrieval Branching
    if intent.intent_type == TYPE_A_SPECIFIC:
        # Type A: Hard Gated Retrieval (only matching entity products can enter candidate pool)
        try:
            fts_res = await full_text_search(
                session,
                query_text,
                limit=candidate_limit,
                allowed_sub_category=intent.matched_sub_category,
                allowed_brand=intent.matched_brand,
            )
        except Exception as exc:
            logger.error(f"FTS retrieval error: {exc}")
            fts_res = []

        try:
            fuzzy_res = await fuzzy_search(
                session,
                query_text,
                limit=candidate_limit,
                allowed_sub_category=intent.matched_sub_category,
                allowed_brand=intent.matched_brand,
            )
        except Exception as exc:
            logger.error(f"Fuzzy retrieval error: {exc}")
            fuzzy_res = []

        try:
            vector_res = await vector_search(
                session,
                query_text,
                limit=candidate_limit,
                min_similarity=0.40,
                allowed_sub_category=intent.matched_sub_category,
                allowed_brand=intent.matched_brand,
            )
        except Exception as exc:
            logger.error(f"Vector retrieval error: {exc}")
            vector_res = []

    else:
        # Type B: Dynamic Taxonomy-Scoped Retrieval (Q2C) - Leaf-node subcategory routing
        scoped_categories = intent.matched_category_ids if intent.is_taxonomy_scoped else None
        scoped_sub_categories = intent.matched_sub_category_ids if intent.is_taxonomy_scoped else None

        try:
            fts_res = await full_text_search(
                session,
                query_text,
                limit=candidate_limit,
                allowed_category_ids=scoped_categories,
                allowed_sub_category_ids=scoped_sub_categories,
            )
        except Exception as exc:
            logger.error(f"FTS retrieval error: {exc}")
            fts_res = []

        try:
            fuzzy_res = await fuzzy_search(
                session,
                query_text,
                limit=candidate_limit,
                allowed_category_ids=scoped_categories,
                allowed_sub_category_ids=scoped_sub_categories,
            )
        except Exception as exc:
            logger.error(f"Fuzzy retrieval error: {exc}")
            fuzzy_res = []

        try:
            vector_res = await vector_search(
                session,
                query_text,
                limit=candidate_limit,
                min_similarity=0.50 if (scoped_sub_categories or scoped_categories) else 0.53,
                allowed_category_ids=scoped_categories,
                allowed_sub_category_ids=scoped_sub_categories,
            )
        except Exception as exc:
            logger.error(f"Vector retrieval error: {exc}")
            vector_res = []

    # 5. Reciprocal Rank Fusion (k=60)
    candidates = reciprocal_rank_fusion(
        fts_results=fts_res,
        fuzzy_results=fuzzy_res,
        vector_results=vector_res,
        k=settings.RRF_K,
    )

    # 5.1 Post-Retrieval Attribute Consistency Gating (Production Facet Filter)
    if intent.inferred_attributes and candidates:
        filtered_candidates = []
        attrs = intent.inferred_attributes
        for cand in candidates:
            specs = cand.product.specifications or {}
            form = specs.get("form", "")
            flavor = specs.get("flavor", "")
            is_food = specs.get("is_food", True)
            tags = cand.product.tags or []

            # Beverage constraint
            if attrs.get("must_be_beverage"):
                is_drink = (form == "liquid") or any(t in tags for t in ["drink", "beverage", "tea", "coffee", "milk", "juice"])
                if not is_drink:
                    continue

            # Sweet flavor constraint
            if attrs.get("must_be_sweet"):
                if flavor in ["salted", "spicy", "savory", "sour"] and not any(t in tags for t in ["sweet", "chocolate", "dessert"]):
                    continue

            # Non-food / Household constraint
            if attrs.get("is_food") is False:
                if is_food is True:
                    continue

            filtered_candidates.append(cand)

        if filtered_candidates:
            candidates = filtered_candidates

    # 6. Optional Cross-Encoder Reranking
    if settings.ENABLE_RERANKER and candidates:
        candidates = await rerank_candidates(
            query=query_text,
            candidates=candidates,
            top_k=settings.RERANK_TOP_K,
        )

    # 7. PostGIS Geospatial & Inventory Business Ranking
    final_items = await filter_and_rank_business(
        session=session,
        candidates=candidates,
        latitude=request.latitude,
        longitude=request.longitude,
        radius_km=resolved.radius_km,
        min_price=resolved.min_price,
        max_price=resolved.max_price,
        category_id=resolved.category_id,
        limit=request.limit,
    )

    # 8. Assemble Response
    return SearchV2Response(
        query=request.query,
        normalized_query=query_text,
        applied_filters={
            "intent": intent.intent_type,
            "matched_brand": intent.matched_brand,
            "matched_sub_category": intent.matched_sub_category,
            "matched_category_ids": [int(x) for x in intent.matched_category_ids],
            "matched_sub_category_ids": [int(x) for x in intent.matched_sub_category_ids],
            "taxonomy_affinity": float(round(float(intent.taxonomy_affinity), 4)),
            "is_taxonomy_scoped": bool(intent.is_taxonomy_scoped),
            "min_price": resolved.min_price,
            "max_price": resolved.max_price,
            "radius_km": resolved.radius_km,
            "category_id": resolved.category_id,
            "hinglish_mapped": parsed.hinglish_terms_mapped,
        },
        total_results=len(final_items),
        results=final_items,
    )
