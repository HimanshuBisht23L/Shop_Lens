from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.product import Product
from db.models.inventory import Inventory
from db.models.store import Store

from apis.v1.schemas.search import UIFilters

from services.search_flow.normalizer import normalize_query
from services.search_flow.filter_resolver import resolve_filters
from services.search_flow.keyword_search import keyword_search
from services.search_flow.fuzzy_search import fuzzy_search
from services.search_flow.geo import user_point


async def search_products(
    session: AsyncSession,
    query: str,
    ui_filters: UIFilters,
    latitude: float,
    longitude: float,
    limit: int = 20,
):

    # Normalize natural-language query
    parsed_query = normalize_query(query)


    # Resolve UI filters vs query filters
    final_filters = resolve_filters(
        parsed_query,
        ui_filters,
    )


    # Keyword candidates
    keyword_products = await keyword_search(
        session=session,
        query=parsed_query.query,
        limit=limit,
    )


    # Fuzzy candidates
    fuzzy_results = await fuzzy_search(
        session=session,
        query=parsed_query.query,
        limit=limit,
    )


    # Combine candidates + scores
    candidate_scores: dict[int, float] = {}

    # Keyword match gets score 1.0
    for product in keyword_products:

        candidate_scores[product.id] = 1.0


    # Fuzzy match gets similarity score
    for product, similarity in fuzzy_results:

        similarity = float(similarity)

        existing_score = candidate_scores.get(
            product.id,
            0.0,
        )

        candidate_scores[product.id] = max(
            existing_score,
            similarity,
        )


    # No candidates
    if not candidate_scores:

        return {
            "query": parsed_query.query,
            "filters": final_filters.model_dump(),
            "results": [],
        }


    # User location
    point = user_point(
        latitude,
        longitude,
    )


    # Distance expression
    distance_expr = func.ST_Distance(
        Store.location,
        point,
    )


    # Product → Inventory → Store
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
            Product.id.in_(
                candidate_scores.keys()
            )
        )
        .where(
            Inventory.is_available.is_(True),
            Inventory.quantity > 0,
            Store.is_active.is_(True),
        )
    )


    # Price filters
    if final_filters.min_price is not None:

        stmt = stmt.where(
            Inventory.price >= final_filters.min_price
        )


    if final_filters.max_price is not None:

        stmt = stmt.where(
            Inventory.price <= final_filters.max_price
        )



    # Optional radius filter
    if final_filters.radius_km is not None:

        radius_meters = (
            final_filters.radius_km * 1000
        )

        stmt = stmt.where(
            func.ST_DWithin(
                Store.location,
                point,
                radius_meters,
            )
        )


    # Always sort by nearest store
    stmt = stmt.order_by(
        distance_expr.asc()
    )


    # Limit final results
    stmt = stmt.limit(limit)


    # Execute query
    result = await session.execute(stmt)

    rows = result.all()


    # Build response
    results = []

    for row in rows:

        product = row[0]
        inventory = row[1]
        store = row[2]
        distance_m = row[3]


        results.append(
            {
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

                "score": candidate_scores.get(
                    product.id,
                    0.0,
                ),
            }
        )


    # Return final response
    return {
        "query": parsed_query.query,
        "filters": final_filters.model_dump(),
        "results": results,
    }