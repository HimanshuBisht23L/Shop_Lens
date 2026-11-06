from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base
# from db.models.attribute import Attribute
# from db.models.product import Product


class ProductAttribute(Base):
    __tablename__ = "product_attributes"

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        primary_key=True,
    )

    attribute_id: Mapped[int] = mapped_column(
        ForeignKey("attributes.id", ondelete="CASCADE"),
        primary_key=True,
    )

    product: Mapped["Product"] = relationship(
        "Product",
        back_populates="product_attributes",
    )

    attribute: Mapped["Attribute"] = relationship(
        "Attribute",
        back_populates="product_attributes",
    )
