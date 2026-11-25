"""Truy vấn đơn hàng và các dòng hàng đã lưu."""
import uuid
from collections import defaultdict
from datetime import datetime

from sqlalchemy import select, tuple_
from sqlalchemy.orm import Session
from sqlalchemy.sql import ColumnElement

from catalog.model import Shop
from orders.model import Order, OrderItem, OrderStatus
from orders.payments.model import AllocationStatus, PaymentAllocation
from orders.schema import OrderItemOut, OrderOut, OrderShopOut, ShippingOut
from reviews.model import Review


def list_shop_orders(
    s: Session, shop_id: uuid.UUID, *, status: OrderStatus | None,
    after: tuple[datetime, uuid.UUID] | None, limit: int,
) -> list[Order]:
    return _list_orders(s, Order.shop_id == shop_id, status=status, after=after, limit=limit)


def list_buyer_orders(
    s: Session, buyer_id: uuid.UUID, *, status: OrderStatus | None,
    after: tuple[datetime, uuid.UUID] | None, limit: int,
) -> list[Order]:
    return _list_orders(s, Order.buyer_id == buyer_id, status=status, after=after, limit=limit)


def _list_orders(
    s: Session, owner_filter: ColumnElement[bool], *, status: OrderStatus | None,
    after: tuple[datetime, uuid.UUID] | None, limit: int,
) -> list[Order]:
    stmt = (
        select(Order).where(owner_filter)
        .order_by(Order.created_at.desc(), Order.id.desc()).limit(limit + 1)
    )
    if status is not None:
        stmt = stmt.where(Order.status == status.value)
    if after is not None:
        stmt = stmt.where(tuple_(Order.created_at, Order.id) < tuple_(*after))
    return list(s.scalars(stmt))


def find_order(s: Session, order_id: uuid.UUID) -> tuple[Order, Shop] | None:
    row = s.execute(select(Order, Shop).join(Shop, Shop.id == Order.shop_id).where(Order.id == order_id)).one_or_none()
    return (row[0], row[1]) if row is not None else None


def lock_seller_order(s: Session, order_id: uuid.UUID, owner_id: uuid.UUID) -> tuple[Order, Shop] | None:
    row = s.execute(
        select(Order, Shop).join(Shop, Shop.id == Order.shop_id)
        .where(Order.id == order_id, Shop.owner_user_id == owner_id)
        .with_for_update(of=Order)
    ).one_or_none()
    return (row[0], row[1]) if row is not None else None


def order_exists(s: Session, order_id: uuid.UUID) -> bool:
    return s.scalar(select(Order.id).where(Order.id == order_id)) is not None


def describe_orders(s: Session, orders: list[Order], shop: Shop | None = None) -> list[OrderOut]:
    if not orders:
        return []

    reviewed = select(Review.id).where(Review.order_item_id == OrderItem.id).exists()
    lines = s.execute(
        select(OrderItem, reviewed).where(OrderItem.order_id.in_([order.id for order in orders]))
        .order_by(OrderItem.created_at, OrderItem.id)
    )
    items_by_order: dict[uuid.UUID, list[OrderItemOut]] = defaultdict(list)
    for item, has_review in lines:
        items_by_order[item.order_id].append(OrderItemOut(
            id=item.id, product_id=item.product_id, product_name=item.product_name,
            unit_price=item.unit_price, quantity=item.quantity, line_total=item.line_total, has_review=has_review,
        ))

    shops = [shop] if shop is not None else s.scalars(select(Shop).where(Shop.id.in_({order.shop_id for order in orders})))
    shops_by_id = {row.id: OrderShopOut.model_validate(row) for row in shops}
    cancelled = [order.id for order in orders if order.status == OrderStatus.CANCELLED.value]
    refunds = {}
    if cancelled:
        refunds = dict(s.execute(
            select(PaymentAllocation.order_id, PaymentAllocation.amount).where(
                PaymentAllocation.order_id.in_(cancelled), PaymentAllocation.status == AllocationStatus.REFUNDED.value,
            )
        ).tuples().all())
    return [
        OrderOut(
            id=order.id, checkout_id=order.checkout_id, shop=shops_by_id[order.shop_id], status=order.status,
            total_amount=order.total_amount,
            shipping=ShippingOut(name=order.shipping_name, phone=order.shipping_phone, address=order.shipping_address),
            items=items_by_order[order.id], paid_at=order.paid_at, shipped_at=order.shipped_at,
            completed_at=order.completed_at, cancelled_at=order.cancelled_at, cancelled_by=order.cancelled_by,
            created_at=order.created_at, refunded_amount=refunds.get(order.id, 0),
        )
        for order in orders
    ]
