from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from db.database import Base


class Inventory(Base):
    __tablename__ = "inventory"


    __table_args__ = (
        Index("idx_inventory_store", "store_id"),
        Index("idx_inventory_product", "product_id"),

        UniqueConstraint(
            "store_id",
            "product_id",
            name="unique_store_product",
        ),

        CheckConstraint(
            "quantity >= 0",
            name="quantity_non_negative",
        ),

        CheckConstraint(
            "price >= 0",
            name="price_non_negative",
        ),
        {
            "comment": 'Store-specific product quantity and price.'
        }
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

    quantity: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False
    )

    price: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )

    is_available: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now,
        onupdate=datetime.now,
        server_default=func.now(),
        nullable=False
    )