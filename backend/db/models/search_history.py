from datetime import datetime

from sqlalchemy import (
    DateTime,
    Double,
    ForeignKey,
    Index,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from db.database import Base


class SearchHistory(Base):
    __tablename__ = "search_history"


    __table_args__ = (
        Index("idx_search_history_user", "user_id"),
        Index("idx_search_history_created", "created_at"),
    )


    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    user_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    query: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    latitude: Mapped[float | None] = mapped_column(
        Double,
        nullable=True
    )

    longitude: Mapped[float | None] = mapped_column(
        Double,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now,
        server_default=func.now(),
        nullable=False
    )