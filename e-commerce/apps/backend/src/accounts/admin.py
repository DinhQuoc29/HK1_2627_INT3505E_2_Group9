"""Nghiệp vụ quản trị người dùng (chỉ admin): xem danh sách, khóa/mở khóa, cấp/thu quyền admin."""
import base64
import logging
import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from accounts import repository
from accounts.model import Role, User, UserStatus
from accounts.schema import AdminUserOut, AdminUserPage
from catalog import repository as catalog_repo
from common.errors import ProblemError
from time_utils import utcnow

log = logging.getLogger("accounts")


def _encode_cursor(user: User) -> str:
    return base64.urlsafe_b64encode(f"{user.created_at.isoformat()}|{user.id}".encode()).decode()


def _decode_cursor(cursor: str) -> tuple[datetime, uuid.UUID]:
    try:
        ts, uid = base64.urlsafe_b64decode(cursor.encode()).decode().split("|")
        return datetime.fromisoformat(ts), uuid.UUID(uid)
    except (ValueError, UnicodeDecodeError):
        raise ProblemError(400, "invalid-cursor", "Cursor không hợp lệ.")


def _out(s: Session, user: User) -> AdminUserOut:
    return AdminUserOut(
        id=user.id, email=user.email, full_name=user.full_name, role=user.role, status=user.status,
        created_at=user.created_at, has_shop=catalog_repo.get_shop_by_owner(s, user.id) is not None,
    )


def list_users(s: Session, *, role, status, q, limit: int, cursor: str | None) -> AdminUserPage:
    rows = repository.list_users(
        s, role=role, status=status, q=(q or "").strip() or None,
        after=_decode_cursor(cursor) if cursor else None, limit=limit,
    )
    page = rows[:limit]
    return AdminUserPage(
        items=[_out(s, u) for u in page],
        next_cursor=_encode_cursor(page[-1]) if len(rows) > limit else None,
    )


def _get(s: Session, user_id: uuid.UUID) -> User:
    user = repository.get_user(s, user_id)
    if user is None:
        raise ProblemError(404, "user-not-found", "Không tìm thấy người dùng.")
    return user


def get_user(s: Session, user_id: uuid.UUID) -> AdminUserOut:
    return _out(s, _get(s, user_id))


def update_user(s: Session, actor: User, user_id: uuid.UUID, role: str | None, status: str | None) -> AdminUserOut:
    user = _get(s, user_id)
    if user.id == actor.id:
        raise ProblemError(409, "cannot-modify-self", "Bạn không thể tự thay đổi vai trò hoặc khóa chính mình.")
    if role is not None and role != user.role:
        if user.role == Role.SELLER.value:
            raise ProblemError(
                409, "seller-has-shop", "Người bán đang có shop nên không đổi vai trò được. Hãy khóa tài khoản nếu cần.",
            )
        repository.set_role(s, user, role)
        log.info("admin_role_changed actor=%s user_id=%s role=%s", actor.id, user.id, role)
    if status is not None and status != user.status:
        repository.set_status(s, user, status)
        if status == UserStatus.SUSPENDED.value:
            repository.revoke_all_sessions(s, user.id, utcnow())  # khóa có hiệu lực ngay
        log.info("admin_status_changed actor=%s user_id=%s status=%s", actor.id, user.id, status)
    return _out(s, user)
