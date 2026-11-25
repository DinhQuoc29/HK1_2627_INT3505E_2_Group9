from datetime import datetime

from orders.model import Checkout, Order, OrderStatus
from orders.payments.model import Payment, PaymentAllocation, PaymentStatus


def capture(checkout: Checkout, orders: list[Order], paid_at: datetime) -> Payment:
    """Lập bản ghi thu tiền mô phỏng trong cùng giao dịch với đơn hàng."""
    for order in orders:
        order.status = OrderStatus.PAID.value
        order.paid_at = paid_at
    return Payment(
        checkout_id=checkout.id, buyer_id=checkout.buyer_id, status=PaymentStatus.SUCCEEDED.value,
        amount=sum(order.total_amount for order in orders), attempt_count=1, paid_at=paid_at,
        allocations=[PaymentAllocation(order_id=order.id, amount=order.total_amount) for order in orders],
    )
