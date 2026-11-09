from datetime import datetime
from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base


class Product(Base):
    __tablename__ = "products"

    __table_args__ = (
        Index("idx_products_category", "category_id"),
        Index("idx_products_sub_category", "sub_category_id"),
        Index("idx_products_brand", "brand"),
        Index("idx_products_sub_category_name", "sub_category_name"),
        Index(
            "idx_products_name_trgm",
            "name",
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        ),
        Index(
            "idx_products_search_vector",
            "search_vector",
            postgresql_using="gin",
        ),
        Index(
            "idx_products_tags",
            "tags",
            postgresql_using="gin",
        ),
        {"comment": "Master product catalog with brand, taxonomy, tags and BGE embeddings."},
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    brand: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    sub_category_id: Mapped[int | None] = mapped_column(
        ForeignKey("sub_categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    sub_category_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    net_quantity: Mapped[str | None] = mapped_column(String(50), nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    tags: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        server_default="{}",
    )
    specifications: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default="{}",
    )

    # 384-d dense vector for BGE-small-en-v1.5
    embedding: Mapped[list[float] | None] = mapped_column(Vector(384), nullable=True)
    search_vector: Mapped[str | None] = mapped_column(TSVECTOR, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    category: Mapped["Category"] = relationship(
        "Category",
        back_populates="products",
    )
    sub_category: Mapped["SubCategory"] = relationship(
        "SubCategory",
        back_populates="products",
    )
    inventory: Mapped[list["Inventory"]] = relationship(
        "Inventory",
        back_populates="product",
        cascade="all, delete-orphan",
    )
