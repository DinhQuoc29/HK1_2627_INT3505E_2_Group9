"""Hủy một đơn của một shop, hoàn kho và hoàn đúng phần đã thu."""
import uuid
from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from catalog.model import Product
from common.errors import ProblemError
from orders import repository
from orders.model import Inventory, Order, OrderItem, OrderStatus
from orders.payments.model import AllocationStatus, Payment, PaymentAllocation, PaymentStatus
from orders.schema import OrderOut
from time_utils import utcnow

_CANCELLABLE = {OrderStatus.PENDING_PAYMENT.value, OrderStatus.PAID.value}
_MAX_INVENTORY = 2_147_483_647


def _restore_inventory(s: Session, order_id: uuid.UUID) -> None:
    rows = [
        {"product_id": product_id, "quantity": quantity}
        for product_id, quantity in s.execute(
            select(OrderItem.product_id, OrderItem.quantity)
            .where(OrderItem.order_id == order_id).order_by(OrderItem.product_id)
        )
    ]
    if not rows:
        return

    # Cùng thứ tự khóa với cập nhật tồn kho và checkout, kể cả khi phải tạo lại dòng tồn kho.
    s.scalars(
        select(Product.id).where(Product.id.in_([row["product_id"] for row in rows]))
        .order_by(Product.id).with_for_update()
    ).all()
    stmt = insert(Inventory).values(rows)
    restored = s.scalars(stmt.on_conflict_do_update(
        index_elements=[Inventory.product_id],
        set_={"quantity": Inventory.quantity + stmt.excluded.quantity, "updated_at": func.now()},
        where=Inventory.quantity <= _MAX_INVENTORY - stmt.excluded.quantity,
    ).returning(Inventory.product_id)).all()
    if len(restored) != len(rows):
        raise ProblemError(409, "inventory-limit", "Chưa thể hoàn kho vì số lượng tồn sẽ vượt giới hạn.")


def cancel(s: Session, order_id: uuid.UUID, actor_id: uuid.UUID, role: Literal["buyer", "seller"]) -> OrderOut:
    found = repository.find_order(s, order_id)
    if found is None:
        raise ProblemError(404, "order-not-found", "Không tìm thấy đơn hàng.")

    order, shop = found
    owner_id = order.buyer_id if role == "buyer" else shop.owner_user_id
    if actor_id != owner_id:
        raise ProblemError(403, "forbidden", "Bạn không có quyền hủy đơn hàng này.")

    # Khóa payment trước để hai lần hủy các đơn cùng lượt mua không ghi đè tổng tiền hoàn.
    payment = s.scalar(
        select(Payment).where(Payment.checkout_id == order.checkout_id).with_for_update()
    )
    # Seller bàn giao cũng khóa dòng Order. Đọc lại sau khi giữ khóa để kiểm tra đúng trạng thái.
    s.refresh(order, with_for_update=True)
    if order.status == OrderStatus.CANCELLED.value:
        return repository.describe_orders(s, [order], shop)[0]
    if order.status not in _CANCELLABLE:
        raise ProblemError(409, "invalid-order-transition", "Chỉ có thể hủy đơn trước khi shop bàn giao để vận chuyển.")

    now = utcnow()
    if order.status == OrderStatus.PAID.value:
        allocation = s.scalar(select(PaymentAllocation).where(PaymentAllocation.order_id == order.id))
        if (
            payment is None or payment.status != PaymentStatus.SUCCEEDED.value or allocation is None
            or allocation.payment_id != payment.id or allocation.status != AllocationStatus.CAPTURED.value
            or allocation.amount != order.total_amount or allocation.amount > payment.amount - payment.refunded_amount
        ):
            raise ProblemError(409, "refund-unavailable", "Thông tin thanh toán chưa khớp để hoàn tiền cho đơn này.")
        allocation.status = AllocationStatus.REFUNDED.value
        allocation.refunded_at = now
        payment.refunded_amount += allocation.amount
    elif payment is not None and payment.status in (PaymentStatus.PENDING.value, PaymentStatus.FAILED.value):
        has_pending_siblings = s.scalar(select(
            select(Order.id).where(
                Order.checkout_id == order.checkout_id, Order.id != order.id,
                Order.status == OrderStatus.PENDING_PAYMENT.value,
            ).exists()
        ))
        if not has_pending_siblings:
            payment.status = PaymentStatus.CANCELLED.value

    _restore_inventory(s, order.id)
    order.status = OrderStatus.CANCELLED.value
    order.cancelled_by = role
    order.cancelled_at = now
    s.flush()
    return repository.describe_orders(s, [order], shop)[0]
