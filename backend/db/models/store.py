from datetime import datetime, time

from geoalchemy2 import Geography # pyright: ignore[reportMissingImports]

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
    Text,
    Time,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship


from typing import TYPE_CHECKING
from db.database import Base

if TYPE_CHECKING:
    from db.models.users import User



class Store(Base):
    __tablename__ = "stores"


    __table_args__ = {
        "comment": 'Local stores registered on ShopLens.'
    }

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    owner_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    address: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    phone: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True
    )

    location = mapped_column(
        Geography(
            geometry_type="POINT",
            srid=4326,
            spatial_index=True
        ),
        nullable=False
    )

    opening_time: Mapped[time | None] = mapped_column(
        Time,
        nullable=True
    )

    closing_time: Mapped[time | None] = mapped_column(
        Time,
        nullable=True
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        nullable=False
    )

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

    # Relationship with User
    owner: Mapped["User"] = relationship(
        "User",
        back_populates="stores",
    )