"""Nghiệp vụ Accounts: đăng ký, đăng nhập, refresh, đăng xuất, Google.

Service chỉ flush; router commit một lần qua session_scope.
"""
import logging
from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from accounts import authentication as auth
from accounts import repository
from accounts.model import AuthSession, Role, User
from common.errors import ProblemError
from config import Settings
from db import new_id
from time_utils import utcnow

log = logging.getLogger("accounts")

_INVALID_CREDENTIALS = ("invalid-credentials", "Email hoặc mật khẩu không đúng.")


@dataclass
class IssuedSession:
    user: User
    access_token: str
    refresh_token: str


def _open_session(s: Session, st: Settings, user: User) -> IssuedSession:
    refresh, refresh_hash = auth.new_refresh_token()
    session = repository.add_session(
        s,
        AuthSession(
            id=new_id(),
            user_id=user.id,
            refresh_token_hash=refresh_hash,
            expires_at=utcnow() + timedelta(days=st.refresh_token_days),
        ),
    )
    return IssuedSession(user, auth.issue_access_token(st, user.id, session.id), refresh)


def register(s: Session, st: Settings, email: str, password: str, full_name: str) -> IssuedSession:
    if repository.get_user_by_email(s, email):
        raise ProblemError(409, "email-already-registered", "Email này đã được đăng ký.")
    user = User(
        id=new_id(), email=email, full_name=full_name,
        password_hash=auth.hash_password(password), role=Role.BUYER.value,
    )
    try:
        repository.add_user(s, user)
    except IntegrityError:  # hai request đăng ký trùng email chạy đồng thời
        raise ProblemError(409, "email-already-registered", "Email này đã được đăng ký.")
    log.info("user_registered user_id=%s", user.id)
    return _open_session(s, st, user)


def login(s: Session, st: Settings, email: str, password: str) -> IssuedSession:
    now = utcnow()
    user = repository.get_user_by_email(s, email)
    if user is None:
        auth.verify_password(password, None)  # cân bằng thời gian, không lộ email có tồn tại
        raise ProblemError(401, *_INVALID_CREDENTIALS)

    if user.locked_until and user.locked_until > now:
        retry = int((user.locked_until - now).total_seconds()) + 1
        raise ProblemError(
            429, "account-locked",
            "Đăng nhập sai quá nhiều lần. Vui lòng thử lại sau.",
            headers={"Retry-After": str(retry)},
        )

    if not auth.verify_password(password, user.password_hash):
        user.failed_login_count += 1
        if user.failed_login_count >= st.login_max_failures:
            user.locked_until = now + timedelta(minutes=st.login_lock_minutes)
            user.failed_login_count = 0
            log.warning("account_locked user_id=%s", user.id)
        s.flush()
        raise ProblemError(401, *_INVALID_CREDENTIALS, persist=True)  # lưu bộ đếm rồi mới trả lỗi

    user.failed_login_count = 0
    user.locked_until = None
    s.flush()
    return _open_session(s, st, user)


def refresh(s: Session, st: Settings, refresh_token: str | None) -> IssuedSession:
    """Xoay vòng refresh token: token cũ mất hiệu lực ngay khi cấp token mới."""
    if not refresh_token:
        raise ProblemError(401, "invalid-refresh-token", "Thiếu refresh token.")
    session = repository.get_session_by_refresh_hash(s, auth.hash_token(refresh_token))
    now = utcnow()
    if session is None or session.revoked_at is not None or session.expires_at <= now:
        raise ProblemError(401, "invalid-refresh-token", "Phiên đã hết hạn, vui lòng đăng nhập lại.")
    user = repository.get_user(s, session.user_id)
    new_refresh, new_hash = auth.new_refresh_token()
    session.refresh_token_hash = new_hash
    s.flush()
    return IssuedSession(user, auth.issue_access_token(st, user.id, session.id), new_refresh)


def logout(s: Session, sid) -> None:
    repository.revoke_session(s, sid, utcnow())


def login_with_google(s: Session, st: Settings, credential: str) -> IssuedSession:
    try:
        claims = auth.verify_google_id_token(credential, st.google_client_id)
    except auth.GoogleUnavailable:
        log.error("google_unavailable")
        raise ProblemError(
            503, "google-unavailable",
            "Không kết nối được tới Google. Tài khoản của bạn vẫn an toàn, vui lòng thử lại.",
            headers={"Retry-After": "5"},
        )
    except ValueError:
        raise ProblemError(401, "invalid-google-token", "Không xác minh được tài khoản Google.")

    subject, email = claims.get("sub"), (claims.get("email") or "").lower()
    if not subject or not email or not claims.get("email_verified"):
        raise ProblemError(401, "invalid-google-token", "Email Google chưa được xác minh.")

    identity = repository.get_identity(s, "google", subject)
    if identity is not None:
        user = repository.get_user(s, identity.user_id)
    else:
        user = repository.get_user_by_email(s, email)  # email Google đã xác minh trùng user có sẵn: liên kết
        if user is None:
            name = (claims.get("name") or email.split("@")[0]).strip()[:100]
            user = repository.add_user(
                s, User(id=new_id(), email=email, full_name=name, password_hash=None, role=Role.BUYER.value)
            )
        repository.add_identity(s, user.id, "google", subject)
    return _open_session(s, st, user)
