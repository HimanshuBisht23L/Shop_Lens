from datetime import datetime

from pydantic import BaseModel, Field


# CREATE PRODUCT
class ProductCreate(BaseModel):

    name: str = Field(
        min_length=2,
        max_length=200,
    )

    normalized_name: str | None = Field(
        default=None,
        max_length=200,
    )

    description: str | None = None

    category_id: int | None = None

    image_url: str | None = None



# UPDATE PRODUCT
class ProductUpdate(BaseModel):

    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=200,
    )

    normalized_name: str | None = Field(
        default=None,
        max_length=200,
    )

    description: str | None = None

    category_id: int | None = None

    image_url: str | None = None



# PRODUCT RESPONSE
class ProductResponse(BaseModel):

    id: int

    name: str

    normalized_name: str | None

    description: str | None

    category_id: int | None

    image_url: str | None

    created_at: datetime

    updated_at: datetime