"""Nghiệp vụ shop của seller. Việc tạo shop nằm ở sellers.service.approve (admin duyệt hồ sơ)."""
import uuid

from sqlalchemy.orm import Session

from catalog import repository
from catalog.model import Shop
from common.errors import ProblemError


def my_shop(s: Session, user_id: uuid.UUID) -> Shop:
    shop = repository.get_shop_by_owner(s, user_id)
    if shop is None:
        raise ProblemError(404, "shop-not-found", "Bạn chưa có shop.")
    return shop


def update_my_shop(s: Session, user_id: uuid.UUID, *, name: str, province_code: str) -> Shop:
    shop = my_shop(s, user_id)
    province = repository.get_province(s, province_code)
    if province is None:
        raise ProblemError(
            422, "validation-error", "Dữ liệu gửi lên không hợp lệ.",
            errors=[{"field": "province_code", "message": "Tỉnh/thành không tồn tại."}],
        )
    shop.name = name
    shop.province = province
    s.flush()
    return shop
