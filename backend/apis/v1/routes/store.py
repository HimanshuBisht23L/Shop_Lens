from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy import func, select, cast
from sqlalchemy.ext.asyncio import AsyncSession

from geoalchemy2 import (
    WKTElement, 
    Geometry
)

from db.database import get_db
from db.models.store import Store
from db.models.users import User


from fastapi import APIRouter

from apis.v1.schemas.store import (
    StoreCreate,
    StoreResponse,
    StoreUpdate,
)

from core.dependencies import get_current_user

router = APIRouter(
    prefix="/stores",
    tags=["Stores"],
)


# CREATE STORE
@router.post(
    "",
    response_model=StoreResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_store( data: StoreCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) :

    # Check whether user already owns a store
    result = await db.execute(
        select(Store).where(
            Store.owner_id == current_user.id
        )
    )

    existing_store = result.scalar_one_or_none()

    if existing_store:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already own a store",
        )

    # Create PostGIS POINT
    # POINT(longitude latitude)
    location = WKTElement(
        f"POINT({data.longitude} {data.latitude})",
        srid=4326,
    )


    # Create store
    store = Store(
        owner_id=current_user.id,
        name=data.name,
        description=data.description,
        address=data.address,
        phone=data.phone,
        location=location,
        opening_time=data.opening_time,
        closing_time=data.closing_time,
        is_active=True,
    )

    db.add(store)

    await db.commit()
    await db.refresh(store)

    return {
        "id": store.id,
        "owner_id": store.owner_id,
        "name": store.name,
        "description": store.description,
        "address": store.address,
        "phone": store.phone,
        "latitude": data.latitude,
        "longitude": data.longitude,
        "opening_time": store.opening_time,
        "closing_time": store.closing_time,
        "is_active": store.is_active,
        "created_at": store.created_at,
        "updated_at": store.updated_at,
    }



# GET MY STORE
@router.get(
    "/me",
    response_model=StoreResponse,
)
async def get_my_store(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) :

    result = await db.execute(
        select(Store).where(
            Store.owner_id == current_user.id
        )
    )

    store = result.scalar_one_or_none()

    if store is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You don't have a store yet",
        )


    # Convert PostGIS location → latitude / longitude
    location_result = await db.execute(
        select(
            func.ST_Y(cast(Store.location, Geometry)).label("latitude"),
            func.ST_X(cast(Store.location, Geometry)).label("longitude"),
        ).where(
            Store.id == store.id
        )
    )

    location = location_result.one()

    return {
        "id": store.id,
        "owner_id": store.owner_id,
        "name": store.name,
        "description": store.description,
        "address": store.address,
        "phone": store.phone,
        "latitude": location.latitude,
        "longitude": location.longitude,
        "opening_time": store.opening_time,
        "closing_time": store.closing_time,
        "is_active": store.is_active,
        "created_at": store.created_at,
        "updated_at": store.updated_at,
    }



# UPDATE MY STORE
@router.put(
    "/me",
    response_model=StoreResponse,
)
async def update_my_store(data: StoreUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) :

    # Find current user's store
    result = await db.execute(
        select(Store).where(
            Store.owner_id == current_user.id
        )
    )

    store = result.scalar_one_or_none()

    if store is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You don't have a store yet",
        )


    # Get only fields that user actually sent
    update_data = data.model_dump(
        exclude_unset=True
    )


    # Update normal fields
    if "name" in update_data:
        store.name = update_data["name"]

    if "description" in update_data:
        store.description = update_data["description"]

    if "address" in update_data:
        store.address = update_data["address"]

    if "phone" in update_data:
        store.phone = update_data["phone"]

    if "opening_time" in update_data:
        store.opening_time = update_data["opening_time"]

    if "closing_time" in update_data:
        store.closing_time = update_data["closing_time"]



    # Update location
    latitude = update_data.get("latitude")
    longitude = update_data.get("longitude")

    if latitude is not None or longitude is not None:

        # If only latitude is provided, keep old longitude
        if latitude is None:
            location_result = await db.execute(
                select(
                    func.ST_Y(cast(Store.location, Geometry)).label("latitude"),
                    func.ST_X(cast(Store.location, Geometry)).label("longitude"),
                ).where(
                    Store.id == store.id
                )
            )

            current_location = location_result.one()
            latitude = current_location.latitude

        # If only longitude is provided, keep old latitude
        if longitude is None:
            location_result = await db.execute(
                select(
                    func.ST_Y(cast(Store.location, Geometry)).label("latitude"),
                    func.ST_X(cast(Store.location, Geometry)).label("longitude"),
                ).where(
                    Store.id == store.id
                )
            )

            current_location = location_result.one()
            longitude = current_location.longitude

        store.location = WKTElement(
            f"POINT({longitude} {latitude})",
            srid=4326,
        )


    await db.commit()
    await db.refresh(store)


    # Get updated coordinates
    location_result = await db.execute(
        select(
            func.ST_Y(cast(Store.location, Geometry)).label("latitude"),
            func.ST_X(cast(Store.location, Geometry)).label("longitude"),
        ).where(
            Store.id == store.id
        )
    )

    location = location_result.one()


    return {
        "id": store.id,
        "owner_id": store.owner_id,
        "name": store.name,
        "description": store.description,
        "address": store.address,
        "phone": store.phone,
        "latitude": location.latitude,
        "longitude": location.longitude,
        "opening_time": store.opening_time,
        "closing_time": store.closing_time,
        "is_active": store.is_active,
        "created_at": store.created_at,
        "updated_at": store.updated_at,
    }



# DEACTIVATE MY STORE
@router.delete(
    "/me",
    status_code=status.HTTP_200_OK,
)
async def deactivate_my_store( current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) :

    # Find current user's store
    result = await db.execute(
        select(Store).where(
            Store.owner_id == current_user.id
        )
    )

    store = result.scalar_one_or_none()

    if store is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You don't have a store yet",
        )


    # Check if already inactive
    if not store.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Store is already inactive",
        )


    # Deactivate store
    store.is_active = False

    await db.commit()

    await db.refresh(store)

    return {
        "message": "Store deactivated successfully"
    }