from datetime import datetime, time

from pydantic import BaseModel, Field


# CREATE STORE
class StoreCreate(BaseModel):

    name: str = Field(
        min_length=2,
        max_length=150,
    )

    description: str | None = None

    address: str = Field(
        min_length=2,
    )

    phone: str | None = Field(
        default=None,
        max_length=20,
    )

    latitude: float = Field(
        ge=-90,
        le=90,
    )

    longitude: float = Field(
        ge=-180,
        le=180,
    )

    opening_time: time | None = None

    closing_time: time | None = None


# STORE RESPONSE
class StoreResponse(BaseModel):

    id: int

    owner_id: int

    name: str

    description: str | None

    address: str

    phone: str | None

    latitude: float

    longitude: float

    opening_time: time | None

    closing_time: time | None

    is_active: bool

    created_at: datetime

    updated_at: datetime



class StoreUpdate(BaseModel):

    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    description: str | None = None

    address: str | None = Field(
        default=None,
        min_length=2,
    )

    phone: str | None = Field(
        default=None,
        max_length=20,
    )

    latitude: float | None = Field(
        default=None,
        ge=-90,
        le=90,
    )

    longitude: float | None = Field(
        default=None,
        ge=-180,
        le=180,
    )

    opening_time: time | None = None

    closing_time: time | None = None