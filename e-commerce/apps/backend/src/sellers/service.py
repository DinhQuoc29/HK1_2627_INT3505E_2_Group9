"""Nghiệp vụ duyệt người bán: buyer (đã xác minh email) nộp hồ sơ -> admin duyệt -> tạo shop + nâng role seller."""
import base64
import logging
import uuid
from datetime import datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from accounts import repository as accounts_repo
from accounts.model import Role, User
from catalog import repository as catalog_repo
from catalog.model import Shop
from common.errors import ProblemError
from db import new_id
from sellers import repository
from sellers.model import ApplicationStatus, SellerApplication
from sellers.schema import AdminApplicationOut, AdminApplicationPage, ApplicationOut
from time_utils import utcnow

log = logging.getLogger("accounts")


def _province_name(s: Session, code: str) -> str:
    p = catalog_repo.get_province(s, code)
    return p.name if p else code


def _out(s: Session, a: SellerApplication) -> ApplicationOut:
    return ApplicationOut(
        id=a.id, shop_name=a.shop_name, province_code=a.province_code, province_name=_province_name(s, a.province_code),
        status=a.status, reject_reason=a.reject_reason, created_at=a.created_at, reviewed_at=a.reviewed_at,
    )


def _admin_out(s: Session, a: SellerApplication, u: User) -> AdminApplicationOut:
    return AdminApplicationOut(
        **_out(s, a).model_dump(), applicant_id=u.id, applicant_email=u.email, applicant_name=u.full_name,
    )


def apply(s: Session, user_id: uuid.UUID, shop_name: str, province_code: str) -> ApplicationOut:
    user = accounts_repo.get_user(s, user_id)
    s.refresh(user, with_for_update=True)  # tuần tự hóa các request đồng thời của cùng một người
    if user.role == Role.ADMIN.value:
        raise ProblemError(403, "forbidden", "Tài khoản quản trị không thể mở shop.")
    if user.role == Role.SELLER.value or catalog_repo.get_shop_by_owner(s, user.id):
        raise ProblemError(409, "shop-already-exists", "Bạn đã có shop.")
    if user.email_verified_at is None:
        raise ProblemError(403, "email-not-verified", "Hãy xác minh email trước khi đăng ký bán hàng.")
    if catalog_repo.get_province(s, province_code) is None:
        raise ProblemError(
            422, "validation-error", "Dữ liệu gửi lên không hợp lệ.",
            errors=[{"field": "province_code", "message": "Tỉnh/thành không tồn tại."}],
        )
    try:
        app = repository.add(s, SellerApplication(id=new_id(), user_id=user.id, shop_name=shop_name, province_code=province_code))
    except IntegrityError:
        raise ProblemError(409, "application-pending", "Bạn đã có hồ sơ đang chờ duyệt.")
    s.refresh(app)
    log.info("seller_application_submitted user_id=%s application_id=%s", user.id, app.id)
    return _out(s, app)


def my_latest(s: Session, user_id: uuid.UUID) -> ApplicationOut:
    app = repository.latest_for_user(s, user_id)
    if app is None:
        raise ProblemError(404, "application-not-found", "Bạn chưa nộp hồ sơ người bán.")
    return _out(s, app)


def _encode(a: SellerApplication) -> str:
    return base64.urlsafe_b64encode(f"{a.created_at.isoformat()}|{a.id}".encode()).decode()


def _decode(cursor: str) -> tuple[datetime, uuid.UUID]:
    try:
        ts, uid = base64.urlsafe_b64decode(cursor.encode()).decode().split("|")
        return datetime.fromisoformat(ts), uuid.UUID(uid)
    except (ValueError, UnicodeDecodeError):
        raise ProblemError(400, "invalid-cursor", "Cursor không hợp lệ.")


def admin_list(s: Session, *, status, limit: int, cursor: str | None) -> AdminApplicationPage:
    rows = repository.list_with_users(s, status=status, after=_decode(cursor) if cursor else None, limit=limit)
    page = rows[:limit]
    return AdminApplicationPage(
        items=[_admin_out(s, a, u) for a, u in page],
        next_cursor=_encode(page[-1][0]) if len(rows) > limit else None,
    )


def _lock_pending(s: Session, app_id: uuid.UUID) -> SellerApplication:
    app = repository.get_for_update(s, app_id)
    if app is None:
        raise ProblemError(404, "application-not-found", "Không tìm thấy hồ sơ.")
    if app.status != ApplicationStatus.PENDING.value:
        raise ProblemError(409, "application-not-pending", "Hồ sơ này đã được xử lý.")
    return app


def approve(s: Session, admin: User, app_id: uuid.UUID) -> tuple[AdminApplicationOut, User, Shop]:
    app = _lock_pending(s, app_id)
    user = accounts_repo.get_user(s, app.user_id)
    s.refresh(user, with_for_update=True)
    if user.role != Role.BUYER.value or catalog_repo.get_shop_by_owner(s, user.id):
        raise ProblemError(409, "applicant-not-eligible", "Người nộp hồ sơ không còn đủ điều kiện mở shop.")
    shop = catalog_repo.add_shop(s, Shop(id=new_id(), owner_user_id=user.id, name=app.shop_name, province_code=app.province_code))
    accounts_repo.set_role(s, user, Role.SELLER.value)
    app.status, app.reviewed_by, app.reviewed_at = ApplicationStatus.APPROVED.value, admin.id, utcnow()
    s.flush()
    s.refresh(app)
    log.info("seller_application_approved admin=%s application_id=%s shop_id=%s", admin.id, app.id, shop.id)
    return _admin_out(s, app, user), user, shop


def reject(s: Session, admin: User, app_id: uuid.UUID, reason: str) -> tuple[AdminApplicationOut, User]:
    app = _lock_pending(s, app_id)
    user = accounts_repo.get_user(s, app.user_id)
    app.status, app.reject_reason = ApplicationStatus.REJECTED.value, reason
    app.reviewed_by, app.reviewed_at = admin.id, utcnow()
    s.flush()
    s.refresh(app)
    log.info("seller_application_rejected admin=%s application_id=%s", admin.id, app.id)
    return _admin_out(s, app, user), user
