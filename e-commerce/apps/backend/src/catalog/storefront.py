"""Đọc sản phẩm công khai và tình trạng tồn kho hiện tại."""
import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, aliased, contains_eager, selectinload

from catalog.model import Category, Product, ProductImage, ProductStatus, Shop
from catalog.schema import CatalogProductCard, CatalogProductDetail, CatalogProductPage
from common.errors import ProblemError
from discovery.search.rule_ranker import rank_products
from orders.model import Inventory


def _published_products(*columns):
    return (
        select(Product, (func.coalesce(Inventory.quantity, 0) > 0).label("in_stock"), *columns)
        .join(Product.shop)
        .join(Shop.province)
        .options(contains_eager(Product.shop).contains_eager(Shop.province))
        .join(Product.category)
        .outerjoin(Inventory, Inventory.product_id == Product.id)
        .where(Product.status == ProductStatus.ACTIVE.value)
    )


def _product_fields(product: Product, in_stock: bool) -> dict:
    return dict(
        id=product.id, name=product.name, brand=product.brand, price=product.price,
        in_stock=in_stock, shop=product.shop,
    )


def list_products(
    s: Session, *, q: str, category: str | None, min_price: int | None,
    max_price: int | None, brand: str | None, province_code: str | None, page: int, limit: int,
) -> CatalogProductPage:
    if min_price is not None and max_price is not None and min_price > max_price:
        raise ProblemError(422, "invalid-price-range", "Giá tối đa phải lớn hơn hoặc bằng giá tối thiểu.")

    parent = aliased(Category)
    cover = (
        select(ProductImage.url).where(ProductImage.product_id == Product.id)
        .order_by(ProductImage.position).limit(1).scalar_subquery()
    )
    stmt = _published_products(cover).outerjoin(parent, parent.id == Category.parent_id)
    if category:
        stmt = stmt.where(or_(Category.slug == category, parent.slug == category))
    if min_price is not None:
        stmt = stmt.where(Product.price >= min_price)
    if max_price is not None:
        stmt = stmt.where(Product.price <= max_price)
    if brand and brand.strip():
        stmt = stmt.where(func.lower(Product.brand) == func.lower(brand.strip()))
    if province_code:
        stmt = stmt.where(Shop.province_code == province_code)

    stmt = rank_products(stmt, q, parent)
    rows = s.execute(stmt.offset((page - 1) * limit).limit(limit + 1)).all()
    return CatalogProductPage(
        items=[
            CatalogProductCard(**_product_fields(product, in_stock), image_url=image_url)
            for product, in_stock, image_url in rows[:limit]
        ],
        has_more=len(rows) > limit,
    )


def product_detail(s: Session, product_id: uuid.UUID) -> CatalogProductDetail:
    parent = aliased(Category)
    row = s.execute(
        _published_products(Category, parent)
        .outerjoin(parent, parent.id == Category.parent_id)
        .options(selectinload(Product.images))
        .where(Product.id == product_id)
    ).one_or_none()
    if row is None:
        raise ProblemError(
            404, "product-not-found", "Sản phẩm không còn được đăng bán hoặc không tồn tại.",
            headers={"Cache-Control": "no-store"},
        )
    product, in_stock, category, parent_category = row
    return CatalogProductDetail(
        **_product_fields(product, in_stock), description=product.description,
        images=[image.url for image in product.images], category=category, parent_category=parent_category,
    )
