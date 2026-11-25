"""Danh mục cấp 2 dùng khi đăng sản phẩm."""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, aliased

from catalog.model import Category
from catalog.schema import ProductCategoryOut
from common.errors import ProblemError


def product_categories(s: Session) -> list[ProductCategoryOut]:
    parent = aliased(Category)
    rows = s.execute(
        select(Category.id, Category.name, parent.name)
        .join(parent, parent.id == Category.parent_id)
        .where(Category.level == 2, parent.level == 1)
        .order_by(parent.name, Category.name, Category.id)
    )
    return [ProductCategoryOut(id=id_, name=name, parent_name=group) for id_, name, group in rows]


def require_product_category(s: Session, category_id: uuid.UUID) -> Category:
    parent = aliased(Category)
    category = s.scalar(
        select(Category).join(parent, parent.id == Category.parent_id)
        .where(Category.id == category_id, Category.level == 2, parent.level == 1)
    )
    if category is None:
        raise ProblemError(422, "invalid-category", "Chọn một danh mục sản phẩm hợp lệ.",
                           errors=[{"field": "category_id", "message": "Danh mục không tồn tại hoặc không phải danh mục cấp 2."}])
    return category
