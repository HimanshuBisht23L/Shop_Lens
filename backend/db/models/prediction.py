from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from db.database import Base


class Prediction(Base):
    __tablename__ = "predictions"


    __table_args__ = (
        Index(
            "idx_predictions_store_product",
            "store_id",
            "product_id",
        ),
        CheckConstraint(
            "predicted_quantity >= 0",
            name="predicted_quantity_non_negative",
        ),

        CheckConstraint(
            "confidence IS NULL OR confidence BETWEEN 0 AND 100",
            name="confidence_valid",
        ),
    )


    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    store_id: Mapped[int] = mapped_column(
        ForeignKey(
            "stores.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey(
            "products.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    predicted_quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    confidence: Mapped[float | None] = mapped_column(
        Numeric(5, 2),
        nullable=True
    )

    prediction_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now,
        server_default=func.now(),
        nullable=False
    )