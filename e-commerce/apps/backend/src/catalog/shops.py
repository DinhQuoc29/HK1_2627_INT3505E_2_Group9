"""Nghiệp vụ shop của seller. Việc tạo shop nằm ở sellers.service.approve (admin duyệt hồ sơ)."""
from sqlalchemy.orm import Session

from catalog import repository
from catalog.model import Shop
from common.errors import ProblemError


def my_shop(s: Session, user_id) -> Shop:
    shop = repository.get_shop_by_owner(s, user_id)
    if shop is None:
        raise ProblemError(404, "shop-not-found", "Bạn chưa có shop.")
    return shop
