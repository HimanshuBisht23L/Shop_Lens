from datetime import datetime, time
from geoalchemy2 import Geography
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    Time,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base


class Store(Base):
    __tablename__ = "stores"

    __table_args__ = (
        Index("idx_stores_location", "location", postgresql_using="gist"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)

    location = mapped_column(
        Geography(geometry_type="POINT", srid=4326),
        nullable=True,
    )

    opening_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    closing_time: Mapped[time | None] = mapped_column(Time, nullable=True)
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

    owner: Mapped["User"] = relationship(
        "User",
        back_populates="stores",
    )
    inventory: Mapped[list["Inventory"]] = relationship(
        "Inventory",
        back_populates="store",
        cascade="all, delete-orphan",
    )
