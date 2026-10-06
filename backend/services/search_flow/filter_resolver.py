from apis.v1.schemas.search import (
    NormalizedQuery,
    SearchFilters,
    UIFilters,
)


def resolve_filters(parsed_query: NormalizedQuery, ui_filters: UIFilters ) -> SearchFilters :

    min_price = (
        ui_filters.min_price
        if ui_filters.min_price is not None
        else parsed_query.min_price
    )

    max_price = (
        ui_filters.max_price
        if ui_filters.max_price is not None
        else parsed_query.max_price
    )

    radius_km = (
        ui_filters.radius_km
        if ui_filters.radius_km is not None
        else parsed_query.radius_km
    )

    return SearchFilters(
        min_price=min_price,
        max_price=max_price,
        radius_km=radius_km,
    )