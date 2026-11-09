from pydantic import BaseModel, Field, model_validator


class NormalizedQuery(BaseModel):
    query: str
    min_price: float | None = None
    max_price: float | None = None
    radius_km: float | None = None


# Sent from UI query parameters
class UIFilters(BaseModel):
    min_price: float | None = None
    max_price: float | None = None
    radius_km: float | None = None


# Applied to database
class SearchFilters(BaseModel):
    min_price: float | None = None
    max_price: float | None = None
    radius_km: float | None = None

    @model_validator(mode="after")
    def validate_filters(self):
        if self.min_price is not None and self.min_price < 0:
            raise ValueError("Minimum price cannot be negative")

        if self.max_price is not None and self.max_price < 0:
            raise ValueError("Maximum price cannot be negative")

        if (
            self.min_price is not None
            and self.max_price is not None
            and self.min_price > self.max_price
        ):
            raise ValueError("Minimum price cannot be greater than maximum price")

        if self.radius_km is not None and self.radius_km <= 0:
            raise ValueError("Radius must be greater than 0")

        return self


class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query string", min_length=1)
    latitude: float = Field(..., ge=-90.0, le=90.0, description="User latitude")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="User longitude")

    min_price: float | None = Field(default=None, ge=0.0, description="Minimum price filter")
    max_price: float | None = Field(default=None, ge=0.0, description="Maximum price filter")
    radius_km: float | None = Field(default=None, gt=0.0, description="Search radius in kilometers")
    category_id: int | None = Field(default=None, description="Optional category filter")
    limit: int = Field(default=20, ge=1, le=100, description="Maximum results to return")

    @model_validator(mode="after")
    def validate_price_range(self):
        if (
            self.min_price is not None
            and self.max_price is not None
            and self.min_price > self.max_price
        ):
            raise ValueError("min_price cannot be greater than max_price")
        return self


# Alias for backward compatibility
SearchV2Request = SearchRequest


class StoreInfo(BaseModel):
    id: int
    name: str
    address: str


class SearchResultItem(BaseModel):
    product_id: int
    product_name: str
    brand: str | None = None
    sub_category_name: str | None = None
    net_quantity: str | None = None
    description: str | None = None
    category_id: int | None = None
    category_name: str | None = None
    price: float
    mrp: float | None = None
    quantity: int
    is_available: bool
    store: StoreInfo
    distance_km: float
    score: float
    sources: list[str] = Field(default_factory=list)


class SearchResponse(BaseModel):
    query: str
    normalized_query: str
    applied_filters: dict
    total_results: int
    results: list[SearchResultItem]


SearchV2Response = SearchResponse
