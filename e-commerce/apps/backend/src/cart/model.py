"""Entity của Cart: các dòng sản phẩm trong giỏ của người mua."""

import uuid

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Index, Integer, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from catalog.model import Product
from db import Base, TimestampMixin


class CartItem(Base, TimestampMixin):
    """Mỗi người mua có một dòng cho mỗi sản phẩm. Lưu giá VND lúc thêm vào giỏ."""

    __tablename__ = "cart_items"
    __table_args__ = (
        PrimaryKeyConstraint("user_id", "product_id", name="pk_cart_items"),
        CheckConstraint("quantity > 0"),
        CheckConstraint("unit_price_at_add > 0"),
        Index("ix_cart_items_product_id", "product_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), primary_key=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price_at_add: Mapped[int] = mapped_column(BigInteger, nullable=False)

    product: Mapped[Product] = relationship()
