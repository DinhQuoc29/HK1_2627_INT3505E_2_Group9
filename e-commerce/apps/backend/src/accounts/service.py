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
from accounts.schema import UserOut
from common.errors import ProblemError
from config import Settings
from db import new_id
from time_utils import utcnow

log = logging.getLogger("accounts")

_INVALID_CREDENTIALS = ("invalid-credentials", "Email hoặc mật khẩu không đúng.")


@dataclass
class IssuedSession:
    user: UserOut
    access_token: str
    refresh_token: str


def profile(s: Session, user: User) -> UserOut:
    """Hồ sơ gửi ra API: không có password_hash; has_password/providers là trường tính toán."""
    return UserOut(
        id=user.id, email=user.email, full_name=user.full_name, role=user.role, created_at=user.created_at,
        providers=repository.list_providers(s, user.id), has_password=bool(user.password_hash),
    )


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
    return IssuedSession(profile(s, user), auth.issue_access_token(st, user.id, session.id), refresh)


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
    return IssuedSession(profile(s, user), auth.issue_access_token(st, user.id, session.id), new_refresh)


def logout(s: Session, sid) -> None:
    repository.revoke_session(s, sid, utcnow())


def _verify_google(st: Settings, credential: str) -> tuple[str, str, dict]:
    """Trả (sub, email, claims) đã xác minh; lỗi Google trả 503 (có thể thử lại) hoặc 401."""
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
    return subject, email, claims


def login_with_google(s: Session, st: Settings, credential: str) -> IssuedSession:
    subject, email, claims = _verify_google(st, credential)
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


def _verify_facebook(st: Settings, access_token: str) -> dict:
    """Trả hồ sơ Facebook đã xác minh; lỗi Facebook trả 503 (có thể thử lại) hoặc 401."""
    try:
        return auth.verify_facebook_token(access_token, st.facebook_app_id, st.facebook_app_secret)
    except auth.FacebookUnavailable:
        log.error("facebook_unavailable")
        raise ProblemError(
            503, "facebook-unavailable",
            "Không kết nối được tới Facebook. Tài khoản của bạn vẫn an toàn, vui lòng thử lại.",
            headers={"Retry-After": "5"},
        )
    except ValueError:
        raise ProblemError(401, "invalid-facebook-token", "Không xác minh được tài khoản Facebook.")


def login_with_facebook(s: Session, st: Settings, access_token: str) -> IssuedSession:
    """Đăng nhập/đăng ký bằng Facebook.

    Khác Google: KHÔNG tự gộp vào tài khoản có sẵn chỉ vì trùng email (email Facebook không có cờ đã-xác-minh
    đáng tin như Google, tự gộp có thể bị lợi dụng chiếm tài khoản). Người dùng phải đăng nhập bằng cách khác
    rồi liên kết Facebook trong trang tài khoản.
    """
    profile = _verify_facebook(st, access_token)
    subject, email = str(profile["id"]), (profile.get("email") or "").strip().lower()
    identity = repository.get_identity(s, "facebook", subject)
    if identity is not None:
        user = repository.get_user(s, identity.user_id)
    else:
        if not email:
            raise ProblemError(
                422, "facebook-email-missing",
                "Tài khoản Facebook chưa chia sẻ email. Hãy cho phép quyền email hoặc đăng ký bằng email.",
            )
        if repository.get_user_by_email(s, email):
            raise ProblemError(
                409, "account-exists",
                "Email của Facebook đã có tài khoản. Hãy đăng nhập bằng mật khẩu hoặc Google, "
                "rồi liên kết Facebook trong trang tài khoản.",
            )
        name = (profile.get("name") or email.split("@")[0]).strip()[:100]
        user = repository.add_user(
            s, User(id=new_id(), email=email, full_name=name, password_hash=None, role=Role.BUYER.value)
        )
        try:
            repository.add_identity(s, user.id, "facebook", subject)
        except IntegrityError:
            raise ProblemError(409, "provider-already-linked", "Tài khoản Facebook này đã được liên kết.")
    return _open_session(s, st, user)


def link_identity(s: Session, st: Settings, user: User, provider: str, credential: str) -> UserOut:
    """Người dùng đã đăng nhập liên kết thêm tài khoản Google/Facebook của mình (SPEC-01)."""
    if provider == "google":
        subject = _verify_google(st, credential)[0]
    elif provider == "facebook":
        subject = str(_verify_facebook(st, credential)["id"])
    else:
        raise ProblemError(404, "identity-not-found", "Nhà cung cấp không được hỗ trợ.")
    label = provider.capitalize()
    existing = repository.get_identity(s, provider, subject)
    if existing is not None:
        if existing.user_id == user.id:
            raise ProblemError(409, "provider-already-linked", f"Tài khoản {label} này đã được liên kết với bạn.")
        raise ProblemError(409, f"{provider}-account-in-use", f"Tài khoản {label} này đã liên kết với một tài khoản khác.")
    if provider in repository.list_providers(s, user.id):
        raise ProblemError(409, "provider-already-linked", f"Bạn đã liên kết một tài khoản {label} khác.")
    try:
        repository.add_identity(s, user.id, provider, subject)
    except IntegrityError:  # hai request liên kết đồng thời
        raise ProblemError(409, "provider-already-linked", f"Tài khoản {label} này đã được liên kết.")
    log.info("identity_linked user_id=%s provider=%s", user.id, provider)
    return profile(s, user)


def unlink_provider(s: Session, user: User, provider: str) -> None:
    linked = repository.list_providers(s, user.id)
    if provider not in linked:
        raise ProblemError(404, "identity-not-found", "Bạn chưa liên kết nhà cung cấp này.")
    # Không để tài khoản mất mọi cách đăng nhập: cần còn mật khẩu hoặc một nhà cung cấp khác.
    if not user.password_hash and len(linked) == 1:
        raise ProblemError(
            409, "last-login-method", "Đây là cách đăng nhập duy nhất của bạn nên không thể hủy liên kết."
        )
    repository.delete_identity(s, user.id, provider)
    log.info("identity_unlinked user_id=%s provider=%s", user.id, provider)
