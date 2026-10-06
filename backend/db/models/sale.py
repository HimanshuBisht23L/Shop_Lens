from datetime import datetime

from sqlalchemy import Index, Integer


from sqlalchemy import (
    DateTime,
    ForeignKey,
    Numeric,
    CheckConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from db.database import Base


class Sale(Base):
    __tablename__ = "sales"


    __table_args__ = (
        Index("idx_sales_store", "store_id"),
        Index("idx_sales_sold_at", "sold_at"),

        CheckConstraint(
            "total_amount >= 0",
            name="sale_total_non_negative",
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

    total_amount: Mapped[float] = mapped_column(
        Numeric(12, 2),
        default=0,
        server_default="0",
        nullable=False
    )

    sold_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now,
        server_default=func.now(),
        nullable=False
    )


class SaleItem(Base):
    __tablename__ = "sale_items"


    __table_args__ = (
        Index("idx_sale_items_sale", "sale_id"),
        Index("idx_sale_items_product", "product_id"),

        CheckConstraint(
            "quantity > 0",
            name="sale_item_quantity_positive",
        ),

        CheckConstraint(
            "unit_price >= 0",
            name="sale_item_price_non_negative",
        ),

        CheckConstraint(
            "subtotal >= 0",
            name="sale_item_subtotal_non_negative",
        ),
    )


    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    sale_id: Mapped[int] = mapped_column(
        ForeignKey(
            "sales.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey(
            "products.id",
            ondelete="RESTRICT"
        ),
        nullable=False
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    unit_price: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )

    subtotal: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )