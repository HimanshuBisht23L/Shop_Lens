from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base


class SubCategory(Base):
    __tablename__ = "sub_categories"

    __table_args__ = (
        Index("idx_sub_categories_category_id", "category_id"),
        {"comment": "Product sub-categories within main categories."},
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    synonyms: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        server_default="{}",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    category: Mapped["Category"] = relationship(
        "Category",
        back_populates="sub_categories",
    )
    products: Mapped[list["Product"]] = relationship(
        "Product",
        back_populates="sub_category",
    )
