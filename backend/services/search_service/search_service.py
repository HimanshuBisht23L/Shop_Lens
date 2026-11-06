
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.product import Product
from db.models.inventory import Inventory
from db.models.store import Store

from services.search_flow.normalizer import normalize_query
from services.search_flow.filter_resolver import resolve_filters
from services.search_flow.keyword_search import keyword_search
from services.search_flow.fuzzy_search import fuzzy_search
from services.search_flow.semantic_search import semantic_search
from services.search_flow.candidate_ranker import rank_candidates
from services.search_flow.geo import user_point


async def search_products(
    session: AsyncSession,
    query: str,
    ui_filters,
    latitude: float,
    longitude: float,
    limit: int = 20,
):
    # --------------------------------------------------
    # 1. Normalize query
    # --------------------------------------------------
    parsed_query = normalize_query(query)

    # --------------------------------------------------
    # 2. Resolve UI filters and natural-language filters
    # --------------------------------------------------
    final_filters = resolve_filters(parsed_query, ui_filters)

    if not parsed_query.query:
        return {
            "query": parsed_query.query,
            "filters": final_filters.model_dump(),
            "results": [],
        }

    # Retrieve more candidates than the final result limit.
    # This reduces the chance that unavailable products
    # prevent relevant nearby products from being returned.
    retrieval_limit = max(limit * 3, 60)

    # --------------------------------------------------
    # 3. Keyword search
    # --------------------------------------------------
    keyword_products = await keyword_search(
        session=session,
        query=parsed_query.query,
        limit=retrieval_limit,
    )

    # --------------------------------------------------
    # 4. Fuzzy search (pg_trgm)
    # --------------------------------------------------
    fuzzy_results = await fuzzy_search(
        session=session,
        query=parsed_query.query,
        limit=retrieval_limit,
    )

    # --------------------------------------------------
    # 5. Semantic search (Sentence Transformer + pgvector)
    # --------------------------------------------------
    semantic_results = await semantic_search(
        session=session,
        query=parsed_query.query,
        limit=retrieval_limit,
    )

    # --------------------------------------------------
    # 6. Merge and rank candidates
    # --------------------------------------------------
    candidate_items = rank_candidates(
        query=parsed_query.query,
        keyword_products=keyword_products,
        fuzzy_results=fuzzy_results,
        semantic_results=semantic_results,
        limit=retrieval_limit,
    )

    candidate_scores = {
        item.product_id: item.final_score
        for item in candidate_items
    }

    if not candidate_scores:
        return {
            "query": parsed_query.query,
            "filters": final_filters.model_dump(),
            "results": [],
        }

    # --------------------------------------------------
    # 7. User location and PostGIS distance
    # --------------------------------------------------
    point = user_point(latitude, longitude)

    distance_expr = func.ST_Distance(
        Store.location,
        point,
    )

    # Convert candidate relevance scores into a SQL ordering expression.
    relevance_order = case(
        candidate_scores,
        value=Product.id,
        else_=0.0,
    )

    # --------------------------------------------------
    # 8. Product + Inventory + Store query
    # --------------------------------------------------
    stmt = (
        select(
            Product,
            Inventory,
            Store,
            distance_expr.label("distance_m"),
        )
        .join(
            Inventory,
            Inventory.product_id == Product.id,
        )
        .join(
            Store,
            Store.id == Inventory.store_id,
        )
        .where(
            Product.id.in_(candidate_scores.keys()),
            Store.location.is_not(None),
            Inventory.is_available.is_(True),
            Inventory.quantity > 0,
            Store.is_active.is_(True),
        )
    )

    # --------------------------------------------------
    # 9. Apply price filters
    # --------------------------------------------------
    if final_filters.min_price is not None:
        stmt = stmt.where(
            Inventory.price >= final_filters.min_price
        )

    if final_filters.max_price is not None:
        stmt = stmt.where(
            Inventory.price <= final_filters.max_price
        )

    # --------------------------------------------------
    # 10. Apply optional radius filter
    # --------------------------------------------------
    if final_filters.radius_km is not None:
        radius_meters = final_filters.radius_km * 1000

        stmt = stmt.where(
            func.ST_DWithin(
                Store.location,
                point,
                radius_meters,
            )
        )

    # --------------------------------------------------
    # 11. Relevance first, nearest store second
    # --------------------------------------------------
    stmt = (
        stmt
        .order_by(
            relevance_order.desc(),
            distance_expr.asc(),
        )
        .limit(limit)
    )

    result = await session.execute(stmt)
    rows = result.all()

    # --------------------------------------------------
    # 12. Build API response
    # --------------------------------------------------
    results = []

    for row in rows:
        product, inventory, store, distance_m = row

        results.append({
            "product_id": product.id,
            "product_name": product.name,
            "description": product.description,
            "price": float(inventory.price),
            "quantity": inventory.quantity,
            "is_available": inventory.is_available,
            "store": {
                "id": store.id,
                "name": store.name,
                "address": store.address,
            },
            "distance_km": round(
                float(distance_m) / 1000,
                2,
            ),
            "score": round(
                candidate_scores.get(product.id, 0.0),
                4,
            ),
        })

    return {
        "query": parsed_query.query,
        "filters": final_filters.model_dump(),
        "results": results,
    }
