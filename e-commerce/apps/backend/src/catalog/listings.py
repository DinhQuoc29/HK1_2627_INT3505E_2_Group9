"""Quản lý sản phẩm thuộc gian hàng của người bán."""
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from catalog import categories, inventory
from catalog.model import Category, Product, ProductImage, ProductStatus
from catalog.schema import ProductInput, ProductState, SellerProductOut, SellerProductPage
from catalog.text import normalize_name
from common.errors import ProblemError
from db import new_id
from orders.model import Inventory
from time_utils import utcnow


def _out(product: Product, category_name: str, quantity: int) -> SellerProductOut:
    return SellerProductOut(
        id=product.id, name=product.name, brand=product.brand, description=product.description,
        category_id=product.category_id, category_name=category_name, price=product.price,
        quantity=quantity, images=[image.url for image in product.images], status=product.status,
    )


def list_products(s: Session, shop_id: uuid.UUID, *, q: str, status: ProductState | None, page: int, limit: int) -> SellerProductPage:
    stmt = (
        select(Product, Category.name, func.coalesce(Inventory.quantity, 0))
        .join(Category, Category.id == Product.category_id)
        .outerjoin(Inventory, Inventory.product_id == Product.id)
        .options(selectinload(Product.images))
        .where(Product.shop_id == shop_id)
        .order_by(Product.created_at.desc(), Product.id.desc())
        .offset((page - 1) * limit).limit(limit + 1)
    )
    if q.strip():
        stmt = stmt.where(Product.name_normalized.contains(normalize_name(q.strip()), autoescape=True))
    if status is not None:
        stmt = stmt.where(Product.status == status)
    rows = s.execute(stmt).all()
    return SellerProductPage(
        items=[_out(product, category, quantity) for product, category, quantity in rows[:limit]],
        has_more=len(rows) > limit,
    )


def _owned_product(s: Session, shop_id: uuid.UUID, product_id: uuid.UUID) -> Product:
    product = s.scalar(
        select(Product).where(Product.id == product_id, Product.shop_id == shop_id)
        .options(selectinload(Product.images)).with_for_update()
    )
    if product is None:
        raise ProblemError(404, "product-not-found", "Không tìm thấy sản phẩm trong gian hàng của bạn.")
    return product


def _save(s: Session, product: Product, body: ProductInput) -> SellerProductOut:
    category = categories.require_product_category(s, body.category_id)
    product.name = body.name
    product.name_normalized = normalize_name(body.name)[:255]
    product.brand = body.brand or None
    product.description = body.description
    product.category_id = category.id
    product.price = body.price
    product.updated_at = utcnow()
    s.add(product)
    current_images = [image.url for image in product.images]
    if current_images != body.images:
        product.images.clear()
        # Xóa các vị trí cũ trước khi gắn ảnh mới để tránh trùng khóa vị trí.
        s.flush()
        product.images.extend(ProductImage(url=url, position=index) for index, url in enumerate(body.images))
    s.flush()
    inventory.put_quantity(s, product.id, body.quantity)
    return _out(product, category.name, body.quantity)


def create_product(s: Session, shop_id: uuid.UUID, body: ProductInput) -> SellerProductOut:
    product = Product(id=new_id(), shop_id=shop_id, status=ProductStatus.ACTIVE.value)
    return _save(s, product, body)


def update_product(s: Session, shop_id: uuid.UUID, product_id: uuid.UUID, body: ProductInput) -> SellerProductOut:
    return _save(s, _owned_product(s, shop_id, product_id), body)


def set_product_status(s: Session, shop_id: uuid.UUID, product_id: uuid.UUID, status: ProductState) -> SellerProductOut:
    product = _owned_product(s, shop_id, product_id)
    if status == ProductStatus.ACTIVE.value and product.status != status:
        categories.require_product_category(s, product.category_id)
        if not product.images or not (product.description or "").strip():
            raise ProblemError(422, "product-incomplete", "Hãy bổ sung mô tả và ảnh trước khi hiển thị sản phẩm.")
    product.status = status
    stock = s.get(Inventory, product.id)
    return _out(product, product.category.name, stock.quantity if stock is not None else 0)
