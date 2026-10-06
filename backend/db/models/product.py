from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from db.database import Base


class Product(Base):
    __tablename__ = "products"



    __table_args__ = (
        Index(
            "idx_products_category",
            "category_id",
        ),

        Index(
            "idx_products_name_trgm",
            "name",
            postgresql_using="gin",
            postgresql_ops={
                "name": "gin_trgm_ops"
            },
        ),

        Index(
            "idx_products_normalized_name_trgm",
            "normalized_name",
            postgresql_using="gin",
            postgresql_ops={
                "normalized_name": "gin_trgm_ops"
            },
        ),
        {
            "comment": 'Master product catalog shared across stores.'
        }       
    )


    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    normalized_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    category_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "categories.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    image_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # Semantic-search embedding will be added later
    # when pgvector is implemented.

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now,
        server_default=func.now(),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now,
        onupdate=datetime.now,
        server_default=func.now(),
        nullable=False
    )