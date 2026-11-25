"""Ghi nhận bàn giao và hoàn tất theo trạng thái hiện tại của đơn."""
import uuid

from sqlalchemy.orm import Session

from common.errors import ProblemError
from orders import repository
from orders.model import OrderStatus
from orders.schema import OrderOut
from time_utils import utcnow

_TRANSITIONS = {
    OrderStatus.SHIPPING: (OrderStatus.PAID, "shipped_at", "Chỉ đơn đã thanh toán mới có thể chuyển sang đang giao."),
    OrderStatus.COMPLETED: (OrderStatus.SHIPPING, "completed_at", "Chỉ đơn đang giao mới có thể xác nhận đã giao."),
}


def advance(s: Session, order_id: uuid.UUID, owner_id: uuid.UUID, destination: OrderStatus) -> OrderOut:
    locked = repository.lock_seller_order(s, order_id, owner_id)
    if locked is None:
        if repository.order_exists(s, order_id):
            raise ProblemError(403, "forbidden", "Đơn hàng không thuộc gian hàng của bạn.")
        raise ProblemError(404, "order-not-found", "Không tìm thấy đơn hàng.")

    order, shop = locked
    expected, date_field, message = _TRANSITIONS[destination]
    if order.status != expected.value:
        raise ProblemError(409, "invalid-order-transition", message)

    order.status = destination.value
    setattr(order, date_field, utcnow())
    s.flush()
    return repository.describe_orders(s, [order], shop)[0]
