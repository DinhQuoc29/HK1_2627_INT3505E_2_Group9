"""Truy cập dữ liệu Accounts. Chỉ module này ghi vào users, user_identities, auth_sessions, privacy_settings."""
import uuid
from datetime import datetime

from sqlalchemy import delete, or_, select, tuple_, update
from sqlalchemy.orm import Session

from accounts.model import AuthSession, EmailToken, PrivacySettings, User, UserIdentity


def get_user_by_email(s: Session, email: str) -> User | None:
    return s.scalar(select(User).where(User.email == email))


def get_user(s: Session, user_id: uuid.UUID) -> User | None:
    return s.get(User, user_id)


def add_user(s: Session, user: User) -> User:
    s.add(user)
    s.add(PrivacySettings(user=user))  # đăng ký luôn tạo privacy_settings
    s.flush()
    return user


def get_identity(s: Session, provider: str, subject: str) -> UserIdentity | None:
    return s.scalar(
        select(UserIdentity).where(
            UserIdentity.provider == provider, UserIdentity.provider_subject == subject
        )
    )


def add_identity(s: Session, user_id: uuid.UUID, provider: str, subject: str) -> UserIdentity:
    identity = UserIdentity(user_id=user_id, provider=provider, provider_subject=subject)
    s.add(identity)
    s.flush()
    return identity


def add_session(s: Session, session: AuthSession) -> AuthSession:
    s.add(session)
    s.flush()
    return session


def get_session_by_refresh_hash(s: Session, token_hash: str) -> AuthSession | None:
    return s.scalar(select(AuthSession).where(AuthSession.refresh_token_hash == token_hash))


def get_active_session_with_user(s: Session, sid: uuid.UUID, now: datetime):
    """Phiên còn hiệu lực (chưa thu hồi, chưa hết hạn) kèm user; None nếu không."""
    return s.execute(
        select(AuthSession, User)
        .join(User, User.id == AuthSession.user_id)
        .where(
            AuthSession.id == sid,
            AuthSession.revoked_at.is_(None),
            AuthSession.expires_at > now,
        )
    ).first()


def revoke_session(s: Session, sid: uuid.UUID, now: datetime) -> None:
    s.execute(
        update(AuthSession)
        .where(AuthSession.id == sid, AuthSession.revoked_at.is_(None))
        .values(revoked_at=now)
    )


def list_providers(s: Session, user_id: uuid.UUID) -> list[str]:
    return list(s.scalars(select(UserIdentity.provider).where(UserIdentity.user_id == user_id).order_by(UserIdentity.provider)))


def delete_identity(s: Session, user_id: uuid.UUID, provider: str) -> int:
    return s.execute(
        delete(UserIdentity).where(UserIdentity.user_id == user_id, UserIdentity.provider == provider)
    ).rowcount


def set_role(s: Session, user: User, role: str) -> None:
    user.role = role
    s.flush()


def revoke_all_sessions(s: Session, user_id: uuid.UUID, now: datetime, except_sid: uuid.UUID | None = None) -> None:
    stmt = update(AuthSession).where(AuthSession.user_id == user_id, AuthSession.revoked_at.is_(None))
    if except_sid is not None:
        stmt = stmt.where(AuthSession.id != except_sid)
    s.execute(stmt.values(revoked_at=now))


def set_status(s: Session, user: User, status: str) -> None:
    user.status = status
    s.flush()


def set_password_hash(s: Session, user: User, password_hash: str) -> None:
    user.password_hash = password_hash
    user.failed_login_count = 0
    user.locked_until = None
    s.flush()


def _like_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def list_users(s: Session, *, role=None, status=None, q=None, after=None, limit: int = 20) -> list[User]:
    """Mới nhất trước; `after` = (created_at, id) của dòng cuối trang trước. Lấy limit + 1 dòng để biết còn trang sau."""
    stmt = select(User).order_by(User.created_at.desc(), User.id.desc()).limit(limit + 1)
    if role:
        stmt = stmt.where(User.role == role)
    if status:
        stmt = stmt.where(User.status == status)
    if q:
        like = f"%{_like_escape(q.lower())}%"
        stmt = stmt.where(or_(User.email.like(like, escape="\\"), User.full_name.ilike(like, escape="\\")))
    if after:
        stmt = stmt.where(tuple_(User.created_at, User.id) < tuple_(after[0], after[1]))
    return list(s.scalars(stmt))


def latest_email_token(s: Session, user_id: uuid.UUID, purpose: str) -> EmailToken | None:
    return s.scalar(
        select(EmailToken).where(EmailToken.user_id == user_id, EmailToken.purpose == purpose)
        .order_by(EmailToken.created_at.desc()).limit(1)
    )


def add_email_token(s: Session, token: EmailToken) -> EmailToken:
    # Token mới thay thế các token cũ chưa dùng cùng mục đích (link cũ hết hiệu lực).
    s.execute(
        update(EmailToken)
        .where(EmailToken.user_id == token.user_id, EmailToken.purpose == token.purpose, EmailToken.used_at.is_(None))
        .values(used_at=token.created_at or datetime.now().astimezone())
    )
    s.add(token)
    s.flush()
    return token


def consume_email_token(s: Session, token_hash: str, purpose: str, now: datetime) -> uuid.UUID | None:
    """Đánh dấu đã dùng NGUYÊN TỬ (chống hai request cùng dùng một token); trả user_id hoặc None."""
    return s.scalar(
        update(EmailToken)
        .where(
            EmailToken.token_hash == token_hash, EmailToken.purpose == purpose,
            EmailToken.used_at.is_(None), EmailToken.expires_at > now,
        )
        .values(used_at=now)
        .returning(EmailToken.user_id)
    )


def mark_email_verified(s: Session, user: User, now: datetime) -> None:
    if user.email_verified_at is None:
        user.email_verified_at = now
        s.flush()
