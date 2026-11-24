"""Entity của module Order & Inventory: inventories, checkouts, orders, order_items.
"""
import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db import Base, CreatedAtMixin, TimestampMixin, new_id


class OrderStatus(str, Enum):
    PENDING_PAYMENT = "pending_payment"
    PAID = "paid"
    SHIPPING = "shipping"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Inventory(Base):
    """Tồn kho, 1-1 với product; chưa có dòng = tồn 0. CHECK là chốt chặn chống tồn âm."""

    __tablename__ = "inventories"
    __table_args__ = (CheckConstraint("quantity >= 0", name="ck_inventories_quantity"),)

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), primary_key=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class Checkout(Base, CreatedAtMixin):
    """Một lượt xác nhận mua; gom các order tách theo shop."""

    __tablename__ = "checkouts"
    __table_args__ = (
        UniqueConstraint("buyer_id", "idempotency_key", name="uq_checkouts_buyer_key"),
        CheckConstraint("total_amount >= 0"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_id)
    buyer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    idempotency_key: Mapped[str] = mapped_column(String(64), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # CHAR(64) SHA-256
    total_amount: Mapped[int] = mapped_column(BigInteger, nullable=False)

    orders: Mapped[list["Order"]] = relationship(back_populates="checkout")


class Order(Base, TimestampMixin):
    """Đơn của một shop trong một checkout; có state machine."""

    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint("checkout_id", "shop_id", name="uq_orders_checkout_shop"),
        CheckConstraint(
            "status IN ('pending_payment','paid','shipping','completed','cancelled')",
            name="ck_orders_status",
        ),
        CheckConstraint("total_amount >= 0", name="ck_orders_total_amount"),
        CheckConstraint("cancelled_by IN ('buyer','seller')", name="ck_orders_cancelled_by"),
        CheckConstraint(
            "(status = 'cancelled' AND cancelled_at IS NOT NULL AND cancelled_by IS NOT NULL)"
            " OR (status <> 'cancelled' AND cancelled_at IS NULL AND cancelled_by IS NULL)",
            name="ck_orders_cancel_fields",
        ),
        CheckConstraint(
            "status NOT IN ('paid','shipping','completed') OR paid_at IS NOT NULL",
            name="ck_orders_paid_at",
        ),
        CheckConstraint(
            "status NOT IN ('shipping','completed') OR shipped_at IS NOT NULL",
            name="ck_orders_shipped_at",
        ),
        CheckConstraint(
            "(status = 'completed') = (completed_at IS NOT NULL)", name="ck_orders_completed_at"
        ),
        Index("ix_orders_buyer_id", "buyer_id"),
        Index("ix_orders_shop_id", "shop_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_id)
    checkout_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("checkouts.id", ondelete="RESTRICT"), nullable=False
    )
    buyer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    shop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shops.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        Text, nullable=False, default=OrderStatus.PENDING_PAYMENT.value,
        server_default=OrderStatus.PENDING_PAYMENT.value,
    )
    total_amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    shipping_name: Mapped[str] = mapped_column(String(100), nullable=False)
    shipping_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    shipping_address: Mapped[str] = mapped_column(String(500), nullable=False)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    shipped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_by: Mapped[str | None] = mapped_column(Text)

    checkout: Mapped[Checkout] = relationship(back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )


class OrderItem(Base, CreatedAtMixin):
    """Dòng hàng của đơn; lưu snapshot tên/giá/số lượng."""

    __tablename__ = "order_items"
    __table_args__ = (
        UniqueConstraint("order_id", "product_id", name="uq_order_items_order_product"),
        CheckConstraint("unit_price > 0", name="ck_order_items_unit_price"),
        CheckConstraint("quantity > 0", name="ck_order_items_quantity"),
        CheckConstraint("line_total = unit_price * quantity", name="ck_order_items_line_total"),
        Index("ix_order_items_product_id", "product_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_id)
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False
    )
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    unit_price: Mapped[int] = mapped_column(BigInteger, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    line_total: Mapped[int] = mapped_column(BigInteger, nullable=False)

    order: Mapped[Order] = relationship(back_populates="items")
