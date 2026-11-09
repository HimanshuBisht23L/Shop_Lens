"""
Business Ranker & Geospatial Inventory Filter for ShopLens Search V2.

Combines semantic and keyword relevance with real-world business constraints:
1. Geospatial filtering:
   - If radius_km is explicitly provided: enforces PostGIS ST_DWithin(Store.location, user_geo, radius_meters).
   - If radius_km is None (not explicitly requested): computes distance to all active stores without artificial radius cutoff.
2. Accurate distance: Computes geodesic distance in km using ST_Distance.
3. Inventory binding: Selects the optimal store (in-stock preferred, nearest distance).
4. Price and Category constraints: Enforces min_price, max_price, category_id.
5. Final Scoring:
   score = relevance_score * (1.0 / (1.0 + DISTANCE_PENALTY_WEIGHT * distance_km)) * stock_factor
"""

from typing import Sequence
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from db.models.store import Store
from db.models.inventory import Inventory
from db.models.product import Product
from db.models.category import Category
from apis.v1.schemas.search import SearchResultItem, StoreInfo
from services.search.ranking.rrf import RankedCandidate


async def filter_and_rank_business(
    session: AsyncSession,
    candidates: list[RankedCandidate],
    latitude: float,
    longitude: float,
    radius_km: float | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    category_id: int | None = None,
    limit: int = settings.DEFAULT_LIMIT,
) -> list[SearchResultItem]:
    if not candidates:
        return []

    # Map candidates by product_id
    candidate_map: dict[int, RankedCandidate] = {
        cand.product.id: cand for cand in candidates
    }
    candidate_ids = list(candidate_map.keys())

    # Build PostGIS point geography: ST_SetSRID(ST_MakePoint(lon, lat), 4326)::geography
    user_geo = func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326).cast(
        Store.location.type
    )

    distance_col = (func.ST_Distance(Store.location, user_geo) / 1000.0).label(
        "distance_km"
    )

    stmt = (
        select(
            Inventory,
            Store,
            distance_col,
            Category.name.label("category_name"),
        )
        .join(Store, Store.id == Inventory.store_id)
        .join(Product, Product.id == Inventory.product_id)
        .outerjoin(Category, Category.id == Product.category_id)
        .where(
            Inventory.product_id.in_(candidate_ids),
            Store.is_active == True,
            Product.is_active == True,
        )
    )

    # Apply radius ONLY when explicitly provided (User Constraint Rule #2)
    if radius_km is not None and radius_km > 0:
        radius_meters = radius_km * 1000.0
        stmt = stmt.where(func.ST_DWithin(Store.location, user_geo, radius_meters))

    if min_price is not None:
        stmt = stmt.where(Inventory.price >= min_price)
    if max_price is not None:
        stmt = stmt.where(Inventory.price <= max_price)
    if category_id is not None:
        stmt = stmt.where(Product.category_id == category_id)

    result = await session.execute(stmt)
    rows = result.all()

    # For each product, pick the best store:
    # 1. in_stock (quantity > 0 and is_available == True) with minimum distance
    # 2. out_of_stock with minimum distance
    product_store_matches: dict[int, tuple[Inventory, Store, float, str | None]] = {}

    for inv, store, dist_km, cat_name in rows:
        pid = inv.product_id
        dist = float(dist_km)
        in_stock = bool(inv.is_available and inv.quantity > 0)

        if pid not in product_store_matches:
            product_store_matches[pid] = (inv, store, dist, cat_name)
            continue

        prev_inv, prev_store, prev_dist, prev_cat = product_store_matches[pid]
        prev_in_stock = bool(prev_inv.is_available and prev_inv.quantity > 0)

        # Prefer in-stock store, otherwise closer store
        if (in_stock and not prev_in_stock) or (in_stock == prev_in_stock and dist < prev_dist):
            product_store_matches[pid] = (inv, store, dist, cat_name)

    # Assemble final SearchResultItem objects
    results: list[SearchResultItem] = []
    penalty_w = settings.DISTANCE_PENALTY_WEIGHT

    for pid, cand in candidate_map.items():
        if pid not in product_store_matches:
            # Not available in any store or failed price/category filter
            continue

        inv, store, dist_km, cat_name = product_store_matches[pid]
        product = cand.product

        # Distance penalty calculation
        dist_factor = 1.0 / (1.0 + penalty_w * dist_km)
        in_stock = bool(inv.is_available and inv.quantity > 0)
        stock_factor = 1.0 if in_stock else 0.5

        final_score = cand.score * dist_factor * stock_factor

        results.append(
            SearchResultItem(
                product_id=product.id,
                product_name=product.name,
                brand=product.brand,
                sub_category_name=product.sub_category_name,
                net_quantity=product.net_quantity,
                description=product.description,
                category_id=product.category_id,
                category_name=cat_name,
                price=float(inv.price),
                mrp=float(inv.mrp) if getattr(inv, "mrp", None) else float(inv.price),
                quantity=inv.quantity,
                is_available=in_stock,
                store=StoreInfo(
                    id=store.id,
                    name=store.name,
                    address=store.address,
                ),
                distance_km=round(dist_km, 2),
                score=round(final_score, 6),
                sources=cand.sources,
            )
        )

    # Sort results by final business score descending
    results.sort(key=lambda item: item.score, reverse=True)
    return results[:limit]
