"""
Filter Resolution Module for ShopLens Search V2.

Reconciles explicit UI filters with parsed natural language filters.
Rules:
1. Explicit UI parameters take precedence over query-extracted filters.
2. If UI filter is absent, fall back to query-extracted filter.
3. Validate bounds (e.g. min_price <= max_price, radius_km > 0).
"""

from dataclasses import dataclass
from services.search.query.normalizer import NormalizedQueryOutput


@dataclass
class ResolvedFilters:
    search_text: str
    min_price: float | None = None
    max_price: float | None = None
    radius_km: float | None = None
    category_id: int | None = None


def resolve_filters(
    parsed: NormalizedQueryOutput,
    ui_min_price: float | None = None,
    ui_max_price: float | None = None,
    ui_radius_km: float | None = None,
    ui_category_id: int | None = None,
    default_radius_km: float = 5.0,
) -> ResolvedFilters:
    # 1. Price resolution
    final_min_price = ui_min_price if ui_min_price is not None else parsed.min_price
    final_max_price = ui_max_price if ui_max_price is not None else parsed.max_price

    if (
        final_min_price is not None
        and final_max_price is not None
        and final_min_price > final_max_price
    ):
        raise ValueError(
            f"min_price ({final_min_price}) cannot exceed max_price ({final_max_price})"
        )

    # 2. Radius resolution: strictly explicit (None if not provided by UI or parsed from query)
    if ui_radius_km is not None:
        final_radius_km = ui_radius_km
    elif parsed.radius_km is not None:
        final_radius_km = parsed.radius_km
    else:
        final_radius_km = None

    if final_radius_km is not None and final_radius_km <= 0:
        raise ValueError(f"radius_km must be positive, got {final_radius_km}")

    return ResolvedFilters(
        search_text=parsed.cleaned_query,
        min_price=final_min_price,
        max_price=final_max_price,
        radius_km=final_radius_km,
        category_id=ui_category_id,
    )
