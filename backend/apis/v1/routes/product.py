from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db.models.product import Product

from apis.v1.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
)

from core.dependencies import get_current_user
from db.models.users import User


router = APIRouter(
    prefix="/products",
    tags=["Products"],
)


# CREATE PRODUCT
@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_product(data: ProductCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) :

    product = Product(
        name=data.name,
        normalized_name=data.normalized_name,
        description=data.description,
        category_id=data.category_id,
        image_url=data.image_url,
    )

    db.add(product)

    await db.commit()
    await db.refresh(product)

    return product



# GET ALL PRODUCTS
@router.get(
    "",
    response_model=list[ProductResponse],
)
async def get_products(db: AsyncSession = Depends(get_db)) :

    result = await db.execute(
        select(Product)
        .order_by(Product.name)
    )

    products = result.scalars().all()

    return products



# GET PRODUCT BY ID
@router.get(
    "/{product_id}",
    response_model=ProductResponse,
)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)) :

    result = await db.execute(
        select(Product).where(
            Product.id == product_id
        )
    )

    product = result.scalar_one_or_none()

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    return product



# UPDATE PRODUCT
@router.put(
    "/{product_id}",
    response_model=ProductResponse,
)
async def update_product(product_id: int, data: ProductUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) :

    result = await db.execute(
        select(Product).where(
            Product.id == product_id
        )
    )

    product = result.scalar_one_or_none()

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )


    # Only update fields actually provided
    update_data = data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(product, field, value)

    await db.commit()
    await db.refresh(product)

    return product