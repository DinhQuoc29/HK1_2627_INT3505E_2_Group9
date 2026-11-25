"""Thống kê đơn và phân bổ thanh toán đã thu của một shop."""
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from orders.model import Order, OrderStatus
from orders.payments.model import AllocationStatus, Payment, PaymentAllocation, PaymentStatus
from orders.schema import ShopStatistics

_PAID_STATUSES = (OrderStatus.PAID.value, OrderStatus.SHIPPING.value, OrderStatus.COMPLETED.value)


def for_shop(s: Session, shop_id: uuid.UUID) -> ShopStatistics:
    captured = (
        (Payment.status == PaymentStatus.SUCCEEDED.value)
        & (PaymentAllocation.status == AllocationStatus.CAPTURED.value)
        & Order.status.in_(_PAID_STATUSES)
    )
    counts = [
        func.count(Order.id).filter(Order.status == status.value).label(status.value)
        for status in OrderStatus
    ]
    summary = s.execute(
        select(
            func.count(Order.id).label("total_orders"),
            *counts,
            func.count(PaymentAllocation.id).filter(captured).label("captured_orders"),
            func.coalesce(func.sum(PaymentAllocation.amount).filter(captured), 0).label("revenue"),
        )
        .select_from(Order)
        .outerjoin(PaymentAllocation, PaymentAllocation.order_id == Order.id)
        .outerjoin(Payment, (Payment.id == PaymentAllocation.payment_id) & (Payment.checkout_id == Order.checkout_id))
        .where(Order.shop_id == shop_id)
    ).mappings().one()

    return ShopStatistics(
        total_orders=summary["total_orders"],
        orders_by_status={status: summary[status.value] for status in OrderStatus},
        captured_orders=summary["captured_orders"],
        recorded_revenue_vnd=str(summary["revenue"]),
    )
