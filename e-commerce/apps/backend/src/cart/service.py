import uuid
from itertools import groupby

from sqlalchemy.orm import Session

from cart import repository
from cart.schema import CartGroup, CartLine, CartOut
from catalog.model import Product, ProductStatus
from common.errors import ProblemError


def get_cart(s: Session, user_id: uuid.UUID) -> CartOut:
    groups = []
    subtotal = 0
    for _, rows in groupby(repository.cart_rows(s, user_id), key=lambda row: row[1].shop_id):
        items = []
        shop_subtotal = 0
        for item, product, stock, image_url in rows:
            active = product.status == ProductStatus.ACTIVE.value
            line_total = item.quantity * product.price
            if active and stock >= item.quantity:
                shop_subtotal += line_total
            items.append(CartLine(
                product_id=product.id, name=product.name, image_url=image_url, quantity=item.quantity,
                is_active=active, available_quantity=stock if active else 0,
                price_changed=product.price != item.unit_price_at_add,
                unit_price_vnd=str(product.price), line_total_vnd=str(line_total),
            ))
        groups.append(CartGroup(shop=product.shop, items=items, subtotal_vnd=str(shop_subtotal)))
        subtotal += shop_subtotal
    return CartOut(groups=groups, subtotal_vnd=str(subtotal))


def _insufficient_stock(stock: int) -> ProblemError:
    detail = f"Sản phẩm hiện còn {stock} món. Vui lòng chọn số lượng phù hợp." if stock else "Sản phẩm đã hết hàng."
    return ProblemError(409, "insufficient-stock", detail)


def _check_quantity(product: Product | None, stock: int, quantity: int) -> None:
    if product is None or product.status != ProductStatus.ACTIVE.value:
        raise ProblemError(409, "product-unavailable", "Sản phẩm không còn được đăng bán.")
    if quantity > stock:
        raise _insufficient_stock(stock)


def add_item(s: Session, user_id: uuid.UUID, product_id: uuid.UUID, quantity: int) -> None:
    product, stock = repository.lock_product_stock(s, product_id)
    if product is None:
        raise ProblemError(404, "product-not-found", "Không tìm thấy sản phẩm.")
    _check_quantity(product, stock, quantity)
    if not repository.increment_item(s, user_id, product, quantity, stock):
        raise ProblemError(
            409, "insufficient-stock",
            f"Số lượng sau khi thêm vượt quá {stock} món hiện có. Hãy kiểm tra giỏ hàng.",
        )


def set_quantity(s: Session, user_id: uuid.UUID, product_id: uuid.UUID, quantity: int) -> None:
    product, stock = repository.lock_product_stock(s, product_id)
    item = repository.lock_item(s, user_id, product_id)
    if item is None:
        raise ProblemError(404, "cart-item-not-found", "Sản phẩm không còn trong giỏ hàng của bạn.")
    _check_quantity(product, stock, quantity)
    item.quantity = quantity
