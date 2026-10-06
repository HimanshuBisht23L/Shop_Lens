from datetime import datetime

from sqlalchemy import (
    Boolean, 
    DateTime, 
    String, 
    Text, 
    func,
)

from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from db.models.store import Store


class User(Base):
    __tablename__ = "users"


    __table_args__ = {
        "comment": 'All ShopLens user accounts. A user can also own/manage a store.'
    }

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    full_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False
    )

    password_hash: Mapped[str] = mapped_column(
        Text,
        nullable=False
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

    # Relationship with Stores
    stores: Mapped[list["Store"]] = relationship(
        "Store",
        back_populates="owner",
        cascade="all, delete-orphan",
    )