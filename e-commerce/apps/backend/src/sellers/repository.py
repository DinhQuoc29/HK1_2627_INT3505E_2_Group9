"""Truy cập dữ liệu Sellers. Chỉ module này ghi vào seller_applications."""
import uuid

from sqlalchemy import select, tuple_
from sqlalchemy.orm import Session

from accounts.model import User
from sellers.model import SellerApplication


def add(s: Session, app: SellerApplication) -> SellerApplication:
    s.add(app)
    s.flush()
    return app


def latest_for_user(s: Session, user_id: uuid.UUID) -> SellerApplication | None:
    return s.scalar(
        select(SellerApplication).where(SellerApplication.user_id == user_id)
        .order_by(SellerApplication.created_at.desc(), SellerApplication.id.desc()).limit(1)
    )


def get_for_update(s: Session, app_id: uuid.UUID) -> SellerApplication | None:
    return s.scalar(select(SellerApplication).where(SellerApplication.id == app_id).with_for_update())


def list_with_users(s: Session, *, status=None, after=None, limit: int = 20):
    """Mới nhất trước, kèm người nộp. Lấy limit + 1 dòng để biết còn trang sau."""
    stmt = (
        select(SellerApplication, User).join(User, User.id == SellerApplication.user_id)
        .order_by(SellerApplication.created_at.desc(), SellerApplication.id.desc()).limit(limit + 1)
    )
    if status:
        stmt = stmt.where(SellerApplication.status == status)
    if after:
        stmt = stmt.where(tuple_(SellerApplication.created_at, SellerApplication.id) < tuple_(after[0], after[1]))
    return list(s.execute(stmt).all())
