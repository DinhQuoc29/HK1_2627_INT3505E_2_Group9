"""Xác nhận toàn bộ giỏ và ghi nhận thanh toán mô phỏng trong một giao dịch."""
import hashlib
import json
import uuid

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from cart.model import CartItem
from cart.repository import lock_buyer_cart
from catalog.model import Product, ProductStatus
from common.errors import ProblemError
from orders import repository
from orders.model import Checkout, Inventory, Order, OrderItem
from orders.payments import simulated_payment
from orders.payments.model import Payment
from orders.schema import MAX_CHECKOUT_AMOUNT, CheckoutOut, CheckoutRequest, PaymentOut
from time_utils import utcnow


def lookup(s: Session, buyer_id: uuid.UUID, key: str) -> Checkout | None:
    return s.scalar(select(Checkout).where(Checkout.buyer_id == buyer_id, Checkout.idempotency_key == key))


def get_owned(s: Session, buyer_id: uuid.UUID, checkout_id: uuid.UUID) -> Checkout:
    checkout = s.get(Checkout, checkout_id)
    if checkout is None:
        raise ProblemError(404, "checkout-not-found", "Không tìm thấy lượt mua.")
    if checkout.buyer_id != buyer_id:
        raise ProblemError(403, "forbidden", "Bạn không có quyền xem lượt mua này.")
    return checkout


def payment_details(s: Session, checkout: Checkout) -> PaymentOut:
    payment = s.scalar(select(Payment).where(Payment.checkout_id == checkout.id))
    if payment is None:
        raise ProblemError(404, "payment-not-found", "Không tìm thấy thanh toán của lượt mua này.")
    return PaymentOut.model_validate(payment)


def describe(s: Session, checkout: Checkout) -> CheckoutOut:
    orders = list(s.scalars(select(Order).where(Order.checkout_id == checkout.id).order_by(Order.id)))
    return CheckoutOut(
        id=checkout.id, total_amount=checkout.total_amount, created_at=checkout.created_at,
        orders=repository.describe_orders(s, orders), payment=payment_details(s, checkout),
    )


def confirm(s: Session, buyer_id: uuid.UUID, key: str, body: CheckoutRequest) -> tuple[Checkout, bool]:
    lock_buyer_cart(s, buyer_id)
    items = sorted(body.items, key=lambda item: item.product_id)
    payload = body.model_dump(mode="json", exclude={"items"})
    payload["items"] = [item.model_dump(mode="json") for item in items]
    request_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    existing = lookup(s, buyer_id, key)
    if existing is not None:
        if existing.request_hash != request_hash:
            raise ProblemError(409, "idempotency-key-conflict", "Mã xác nhận đã được dùng cho nội dung mua hàng khác.")
        return existing, False

    reviewed = {item.product_id: item.quantity for item in items}
    cart = dict(s.execute(
        select(CartItem.product_id, CartItem.quantity).where(CartItem.user_id == buyer_id)
    ).tuples().all())
    if reviewed != cart:
        raise ProblemError(409, "cart-changed", "Giỏ hàng đã thay đổi. Vui lòng xem lại trước khi xác nhận.")

    # Khóa sản phẩm rồi tồn kho theo cùng thứ tự với seller. Thứ tự ID ổn định giữa các buyer.
    products = {p.id: p for p in s.scalars(
        select(Product).where(Product.id.in_(reviewed)).order_by(Product.id).with_for_update()
    )}
    inventories = {stock.product_id: stock for stock in s.scalars(
        select(Inventory).where(Inventory.product_id.in_(reviewed)).order_by(Inventory.product_id).with_for_update()
    )}
    unavailable = [
        str(id_) for id_ in reviewed if id_ not in products or products[id_].status != ProductStatus.ACTIVE.value
    ]
    if unavailable:
        raise ProblemError(
            409, "product-unavailable", "Một số sản phẩm không còn được đăng bán.",
            extensions={"product_ids": unavailable},
        )

    total = sum(products[item.product_id].price * item.quantity for item in items)
    if total > MAX_CHECKOUT_AMOUNT:
        raise ProblemError(422, "amount-too-large", "Tổng tiền vượt giới hạn. Hãy giảm số lượng trong giỏ hàng.")

    changes = [
        {"product_id": str(item.product_id), "expected_unit_price": item.expected_unit_price,
         "current_unit_price": products[item.product_id].price}
        for item in items if products[item.product_id].price != item.expected_unit_price
    ]
    if changes:
        raise ProblemError(
            409, "price-changed", "Giá đã thay đổi. Hãy xem lại tổng tiền và xác nhận giá mới.",
            extensions={"changes": changes},
        )

    shortages = []
    for item in items:
        stock = inventories.get(item.product_id)
        available = stock.quantity if stock is not None else 0
        if available < item.quantity:
            shortages.append({"product_id": str(item.product_id), "requested": item.quantity, "available": available})
    if shortages:
        raise ProblemError(
            409, "insufficient-stock", "Một số sản phẩm không đủ hàng. Hãy cập nhật giỏ hàng.",
            extensions={"products": shortages},
        )

    if body.simulate == "failed":
        raise ProblemError(409, "payment-failed", "Thanh toán mô phỏng thất bại. Vui lòng thử lại.")

    purchase = Checkout(buyer_id=buyer_id, idempotency_key=key, request_hash=request_hash, total_amount=total)
    orders: dict[uuid.UUID, Order] = {}
    for item in items:
        product = products[item.product_id]
        order = orders.get(product.shop_id)
        if order is None:
            order = Order(
                checkout=purchase, buyer_id=buyer_id, shop_id=product.shop_id, total_amount=0,
                shipping_name=body.shipping.name, shipping_phone=body.shipping.phone, shipping_address=body.shipping.address,
            )
            orders[product.shop_id] = order
        line_total = product.price * item.quantity
        order.items.append(OrderItem(
            product_id=product.id, product_name=product.name, unit_price=product.price,
            quantity=item.quantity, line_total=line_total,
        ))
        order.total_amount += line_total
        inventories[product.id].quantity -= item.quantity

    s.add(purchase)
    s.flush()
    s.add(simulated_payment.capture(purchase, list(orders.values()), utcnow()))
    s.execute(delete(CartItem).where(CartItem.user_id == buyer_id))
    s.flush()
    return purchase, True
