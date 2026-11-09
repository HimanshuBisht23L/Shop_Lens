from datetime import datetime
from sqlalchemy import DateTime, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base


class Category(Base):
    __tablename__ = "categories"

    __table_args__ = (
        Index("idx_categories_name", "name", unique=True),
        {"comment": "Product category taxonomy master table."},
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    sub_categories: Mapped[list["SubCategory"]] = relationship(
        "SubCategory",
        back_populates="category",
        cascade="all, delete-orphan",
    )
    products: Mapped[list["Product"]] = relationship(
        "Product",
        back_populates="category",
    )
