from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from apis.v1.schemas.search import UIFilters
from services.search_service.search_service import search_products


router = APIRouter(
    prefix="/search",
    tags=["Search"],
)


@router.get("")
async def search_products_route(
    q: str,

    latitude: float,
    longitude: float,

    min_price: float | None = None,
    max_price: float | None = None,
    radius_km: float | None = None,

    session: AsyncSession = Depends(get_db),
):

    ui_filters = UIFilters(
        min_price=min_price,
        max_price=max_price,
        radius_km=radius_km,
    )

    return await search_products(
        session=session,
        query=q,
        ui_filters=ui_filters,
        latitude=latitude,
        longitude=longitude,
    )