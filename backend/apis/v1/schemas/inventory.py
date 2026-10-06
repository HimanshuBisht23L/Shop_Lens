from datetime import datetime

from pydantic import BaseModel, Field


# CREATE INVENTORY
class InventoryCreate(BaseModel):

    product_id: int = Field(
        gt=0
    )

    quantity: int = Field(
        default=0,
        ge=0,
    )

    price: float = Field(
        gt=0
    )

    is_available: bool = True



# UPDATE INVENTORY
class InventoryUpdate(BaseModel):

    quantity: int | None = Field(
        default=None,
        ge=0,
    )

    price: float | None = Field(
        default=None,
        gt=0,
    )

    is_available: bool | None = None



# INVENTORY RESPONSE
class InventoryResponse(BaseModel):

    id: int

    store_id: int

    product_id: int

    quantity: int

    price: float

    is_available: bool

    updated_at: datetime