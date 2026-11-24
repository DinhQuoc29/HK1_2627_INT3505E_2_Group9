"""Entity của module Cart: cart_items."""
import uuid

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Index, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from db import Base, TimestampMixin


class CartItem(Base, TimestampMixin):
    """Giỏ hàng theo tài khoản; một dòng cho mỗi (user, product)."""

    __tablename__ = "cart_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_cart_items_quantity"),
        CheckConstraint("unit_price_at_add > 0", name="ck_cart_items_unit_price_at_add"),
        Index("ix_cart_items_product_id", "product_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), primary_key=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price_at_add: Mapped[int] = mapped_column(BigInteger, nullable=False)  # VND, giá lúc thêm
