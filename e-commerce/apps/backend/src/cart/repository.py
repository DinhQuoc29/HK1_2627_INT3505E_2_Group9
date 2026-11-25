import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session, contains_eager

from cart.model import CartItem
from catalog.model import Product, ProductImage, Shop
from orders.model import Inventory


def cart_rows(s: Session, user_id: uuid.UUID):
    cover = (
        select(ProductImage.url).where(ProductImage.product_id == Product.id)
        .order_by(ProductImage.position).limit(1).scalar_subquery()
    )
    return s.execute(
        select(CartItem, Product, func.coalesce(Inventory.quantity, 0), cover)
        .join(Product, Product.id == CartItem.product_id)
        .join(Product.shop).join(Shop.province)
        .options(contains_eager(Product.shop).contains_eager(Shop.province))
        .outerjoin(Inventory, Inventory.product_id == Product.id)
        .where(CartItem.user_id == user_id)
        .order_by(Shop.name, Shop.id, CartItem.created_at, Product.id)
    ).all()


def lock_product_stock(s: Session, product_id: uuid.UUID) -> tuple[Product | None, int]:
    # Cùng thứ tự khóa với cập nhật của seller. Khóa đọc cho phép các buyer thêm đồng thời.
    product = s.scalar(select(Product).where(Product.id == product_id).with_for_update(read=True))
    quantity = s.scalar(
        select(Inventory.quantity).where(Inventory.product_id == product_id).with_for_update(read=True)
    ) if product is not None else None
    return product, quantity or 0


def increment_item(
    s: Session, user_id: uuid.UUID, product: Product, quantity: int, available: int,
) -> bool:
    stmt = insert(CartItem).values(
        user_id=user_id, product_id=product.id, quantity=quantity, unit_price_at_add=product.price,
    )
    changed = s.scalar(stmt.on_conflict_do_update(
        index_elements=[CartItem.user_id, CartItem.product_id],
        set_={"quantity": CartItem.quantity + stmt.excluded.quantity, "updated_at": func.now()},
        where=CartItem.quantity <= available - quantity,
    ).returning(CartItem.product_id))
    return changed is not None


def lock_item(s: Session, user_id: uuid.UUID, product_id: uuid.UUID) -> CartItem | None:
    return s.scalar(
        select(CartItem)
        .where(CartItem.user_id == user_id, CartItem.product_id == product_id)
        .with_for_update()
    )


def remove_item(s: Session, user_id: uuid.UUID, product_id: uuid.UUID) -> None:
    s.execute(delete(CartItem).where(CartItem.user_id == user_id, CartItem.product_id == product_id))
