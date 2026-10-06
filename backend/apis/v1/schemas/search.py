from pydantic import BaseModel, model_validator


class NormalizedQuery(BaseModel):
    query: str

    min_price: float | None = None
    max_price: float | None = None

    radius_km: float | None = None



# Which user will send from UI
class UIFilters(BaseModel):

    min_price: float | None = None
    max_price: float | None = None

    radius_km: float | None = None



# Which will applied to database
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
            raise ValueError(
                "Minimum price cannot be greater than maximum price"
            )

        if self.radius_km is not None and self.radius_km <= 0:
            raise ValueError("Radius must be greater than 0")

        return self