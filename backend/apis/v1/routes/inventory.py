from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db.models.inventory import Inventory
from db.models.product import Product
from db.models.store import Store
from db.models.users import User

from apis.v1.schemas.inventory import (
    InventoryCreate,
    InventoryUpdate,
    InventoryResponse,
)

from core.dependencies import get_current_user


router = APIRouter(
    prefix="/inventory",
    tags=["Inventory"],
)

# Helper function to get the store of the current user
async def get_user_store(current_user: User, db: AsyncSession) -> Store :

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

    if not store.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your store is inactive",
        )

    return store



@router.post(
    "",
    response_model=InventoryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_inventory(data: InventoryCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) :

    # Get user's store
    store = await get_user_store(
        current_user,
        db,
    )


    # Check product exists
    result = await db.execute(
        select(Product).where(
            Product.id == data.product_id
        )
    )

    product = result.scalar_one_or_none()

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )


    # Check duplicate inventory
    result = await db.execute(
        select(Inventory).where(
            Inventory.store_id == store.id,
            Inventory.product_id == data.product_id,
        )
    )

    existing_inventory = result.scalar_one_or_none()

    if existing_inventory:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product already exists in your inventory",
        )


    # Create inventory
    inventory = Inventory(
        store_id=store.id,
        product_id=data.product_id,
        quantity=data.quantity,
        price=data.price,
        is_available=data.is_available,
    )

    db.add(inventory)

    await db.commit()
    await db.refresh(inventory)

    return inventory


# Get all inventory items for the current user's store
@router.get(
    "",
    response_model=list[InventoryResponse],
)
async def get_my_inventory(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) :

    store = await get_user_store(
        current_user,
        db,
    )

    result = await db.execute(
        select(Inventory)
        .where(
            Inventory.store_id == store.id
        )
        .order_by(Inventory.id)
    )

    inventory = result.scalars().all()

    return inventory


# Update inventory item for the current user's store
@router.put(
    "/{inventory_id}",
    response_model=InventoryResponse,
)
async def update_inventory(inventory_id: int, data: InventoryUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) :

    store = await get_user_store(
        current_user,
        db,
    )


    # Find inventory belonging to THIS store
    result = await db.execute(
        select(Inventory).where(
            Inventory.id == inventory_id,
            Inventory.store_id == store.id,
        )
    )

    inventory = result.scalar_one_or_none()

    if inventory is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory item not found",
        )


    # Update only supplied fields
    update_data = data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(inventory, field, value)

    await db.commit()
    await db.refresh(inventory)

    return inventory



# Delete inventory item for the current user's store
@router.delete(
    "/{inventory_id}",
)
async def delete_inventory(inventory_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) :

    store = await get_user_store(
        current_user,
        db,
    )

    result = await db.execute(
        select(Inventory).where(
            Inventory.id == inventory_id,
            Inventory.store_id == store.id,
        )
    )

    inventory = result.scalar_one_or_none()

    if inventory is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory item not found",
        )

    await db.delete(inventory)

    await db.commit()

    return {
        "message": "Inventory item removed successfully"
    }