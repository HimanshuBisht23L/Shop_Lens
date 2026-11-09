from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base


class Inventory(Base):
    __tablename__ = "inventory"

    __table_args__ = (
        UniqueConstraint("store_id", "product_id", name="unique_store_product"),
        Index("idx_inventory_store", "store_id"),
        Index("idx_inventory_product", "product_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    quantity: Mapped[int] = mapped_column(default=0, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    mrp: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    product: Mapped["Product"] = relationship(
        "Product",
        back_populates="inventory",
    )
    store: Mapped["Store"] = relationship(
        "Store",
        back_populates="inventory",
    )
