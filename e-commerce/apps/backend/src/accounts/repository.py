"""Truy cập dữ liệu Accounts. Chỉ module này ghi vào users, user_identities, auth_sessions, privacy_settings."""
import uuid
from datetime import datetime

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from accounts.model import AuthSession, PrivacySettings, User, UserIdentity


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
