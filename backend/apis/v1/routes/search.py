from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from apis.v1.schemas.search import SearchRequest, SearchResponse
from services.search.search_service import execute_search


router = APIRouter(
    prefix="/search",
    tags=["Search"],
)


@router.get("", response_model=SearchResponse)
async def search_products_get(
    q: str = Query(..., min_length=1, description="Search query string"),
    latitude: float = Query(..., ge=-90.0, le=90.0, description="User latitude"),
    longitude: float = Query(..., ge=-180.0, le=180.0, description="User longitude"),
    min_price: float | None = Query(None, ge=0.0, description="Minimum price filter"),
    max_price: float | None = Query(None, ge=0.0, description="Maximum price filter"),
    radius_km: float | None = Query(None, gt=0.0, description="Search radius in km"),
    category_id: int | None = Query(None, description="Optional category filter"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results to return"),
    session: AsyncSession = Depends(get_db),
):
    request = SearchRequest(
        query=q,
        latitude=latitude,
        longitude=longitude,
        min_price=min_price,
        max_price=max_price,
        radius_km=radius_km,
        category_id=category_id,
        limit=limit,
    )
    return await execute_search(session=session, request=request)


@router.post("/products", response_model=SearchResponse)
async def search_products_post(
    request: SearchRequest,
    session: AsyncSession = Depends(get_db),
):
    return await execute_search(session=session, request=request)
