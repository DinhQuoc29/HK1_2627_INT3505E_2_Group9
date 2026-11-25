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
from accounts.model import AuthSession, EmailToken, EmailTokenPurpose, Role, User, UserStatus
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
    verify_token: str | None = None  # token xác minh email vừa phát hành (đăng ký mới); route gửi email


def profile(s: Session, user: User) -> UserOut:
    """Hồ sơ gửi ra API: không có password_hash; has_password/providers là trường tính toán."""
    return UserOut(
        id=user.id, email=user.email, full_name=user.full_name, role=user.role, created_at=user.created_at,
        providers=repository.list_providers(s, user.id), has_password=bool(user.password_hash),
        email_verified=user.email_verified_at is not None,
    )


def ensure_active(user: User) -> None:
    if user.status != UserStatus.ACTIVE.value:
        raise ProblemError(403, "account-suspended", "Tài khoản của bạn đã bị tạm khóa. Vui lòng liên hệ quản trị viên.")


def _open_session(s: Session, st: Settings, user: User) -> IssuedSession:
    ensure_active(user)
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
    issued = _open_session(s, st, user)
    issued.verify_token = _issue_email_token(s, user, EmailTokenPurpose.VERIFY_EMAIL, timedelta(hours=st.verify_token_hours))
    return issued


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
    ensure_active(user)
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
    repository.mark_email_verified(s, user, utcnow())  # Google đã xác minh email (email_verified = true)
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


def change_password(s: Session, user: User, sid, current_password: str | None, new_password: str) -> None:
    """Đổi (hoặc đặt lần đầu cho tài khoản chỉ có Google/Facebook) mật khẩu; thu hồi mọi phiên khác."""
    user = repository.get_user(s, user.id)
    if user.password_hash:
        if not current_password or not auth.verify_password(current_password, user.password_hash):
            raise ProblemError(
                422, "validation-error", "Dữ liệu gửi lên không hợp lệ.",
                errors=[{"field": "current_password", "message": "Mật khẩu hiện tại không đúng."}],
            )
        if auth.verify_password(new_password, user.password_hash):
            raise ProblemError(
                422, "validation-error", "Dữ liệu gửi lên không hợp lệ.",
                errors=[{"field": "new_password", "message": "Mật khẩu mới phải khác mật khẩu hiện tại."}],
            )
    repository.set_password_hash(s, user, auth.hash_password(new_password))
    repository.revoke_all_sessions(s, user.id, utcnow(), except_sid=sid)
    log.info("password_changed user_id=%s", user.id)


# ---- Token email: xác minh email và đặt lại mật khẩu ----------------------------------------------------------

def _issue_email_token(s: Session, user: User, purpose: EmailTokenPurpose, ttl: timedelta) -> str:
    raw, token_hash = auth.new_refresh_token()
    now = utcnow()
    repository.add_email_token(s, EmailToken(
        id=new_id(), user_id=user.id, purpose=purpose.value, token_hash=token_hash, expires_at=now + ttl, created_at=now,
    ))
    return raw


def _cooldown_left(s: Session, st: Settings, user: User, purpose: EmailTokenPurpose) -> int:
    last = repository.latest_email_token(s, user.id, purpose.value)
    if last is None:
        return 0
    return max(0, int(st.email_resend_cooldown_seconds - (utcnow() - last.created_at).total_seconds()) + 1)


def request_email_verification(s: Session, st: Settings, user: User) -> str:
    user = repository.get_user(s, user.id)
    if user.email_verified_at is not None:
        raise ProblemError(409, "email-already-verified", "Email của bạn đã được xác minh.")
    wait = _cooldown_left(s, st, user, EmailTokenPurpose.VERIFY_EMAIL)
    if wait:
        raise ProblemError(
            429, "rate-limited", "Bạn vừa yêu cầu gửi email. Vui lòng đợi một chút rồi thử lại.",
            headers={"Retry-After": str(wait)},
        )
    return _issue_email_token(s, user, EmailTokenPurpose.VERIFY_EMAIL, timedelta(hours=st.verify_token_hours))


def confirm_email(s: Session, token: str) -> None:
    now = utcnow()
    user_id = repository.consume_email_token(s, auth.hash_token(token), EmailTokenPurpose.VERIFY_EMAIL.value, now)
    if user_id is None:
        raise ProblemError(400, "invalid-email-token", "Liên kết xác minh không hợp lệ hoặc đã hết hạn.")
    repository.mark_email_verified(s, repository.get_user(s, user_id), now)
    log.info("email_verified user_id=%s", user_id)


def request_password_reset(s: Session, st: Settings, email: str) -> tuple[User, str] | None:
    """Trả (user, token) để gửi email, hoặc None. Route luôn trả 202 như nhau để không lộ email có tồn tại."""
    user = repository.get_user_by_email(s, email)
    if user is None or user.status != UserStatus.ACTIVE.value:
        return None
    if _cooldown_left(s, st, user, EmailTokenPurpose.RESET_PASSWORD):
        return None  # chống dùng tính năng này để spam hộp thư của người khác
    return user, _issue_email_token(s, user, EmailTokenPurpose.RESET_PASSWORD, timedelta(minutes=st.reset_token_minutes))


def confirm_password_reset(s: Session, token: str, new_password: str) -> None:
    now = utcnow()
    user_id = repository.consume_email_token(s, auth.hash_token(token), EmailTokenPurpose.RESET_PASSWORD.value, now)
    if user_id is None:
        raise ProblemError(400, "invalid-reset-token", "Liên kết đặt lại mật khẩu không hợp lệ hoặc đã hết hạn.")
    user = repository.get_user(s, user_id)
    repository.set_password_hash(s, user, auth.hash_password(new_password))
    repository.mark_email_verified(s, user, now)  # đã nhận được email nên đã chứng minh sở hữu địa chỉ
    repository.revoke_all_sessions(s, user.id, now)  # mọi thiết bị phải đăng nhập lại
    log.info("password_reset user_id=%s", user.id)
