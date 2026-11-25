"""Entity của module Accounts: users, user_identities, auth_sessions, privacy_settings."""
import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db import Base, CreatedAtMixin, TimestampMixin, new_id


class Role(str, Enum):
    BUYER = "buyer"
    SELLER = "seller"
    ADMIN = "admin"


class UserStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"


class User(Base, TimestampMixin):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('buyer','seller','admin')", name="ck_users_role"),
        CheckConstraint("status IN ('active','suspended')", name="ck_users_status"),
        Index("ix_users_created_at_id", "created_at", "id"),
        CheckConstraint("failed_login_count >= 0", name="ck_users_failed_login_count"),
        CheckConstraint("email = lower(email)", name="ck_users_email_lower"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_id)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str | None] = mapped_column(String(100))  # NULL: chỉ đăng nhập Google
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(
        Text, nullable=False, default=Role.BUYER.value, server_default=Role.BUYER.value
    )
    status: Mapped[str] = mapped_column(
        Text, nullable=False, default=UserStatus.ACTIVE.value, server_default=UserStatus.ACTIVE.value
    )
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failed_login_count: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=0, server_default="0"
    )
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    identities: Mapped[list["UserIdentity"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    sessions: Mapped[list["AuthSession"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    privacy_settings: Mapped["PrivacySettings | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True, uselist=False
    )


class UserIdentity(Base, CreatedAtMixin):
    """Liên kết tài khoản với nhà cung cấp OAuth (Google, Facebook)."""

    __tablename__ = "user_identities"
    __table_args__ = (
        CheckConstraint("provider IN ('google', 'facebook')", name="ck_user_identities_provider"),
        UniqueConstraint("provider", "provider_subject", name="uq_user_identities_provider_subject"),
        UniqueConstraint("user_id", "provider", name="uq_user_identities_user_provider"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_id)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    provider: Mapped[str] = mapped_column(Text, nullable=False)
    provider_subject: Mapped[str] = mapped_column(String(255), nullable=False)

    user: Mapped[User] = relationship(back_populates="identities")


class AuthSession(Base, TimestampMixin):
    """Phiên đăng nhập; id chính là claim `sid` trong access token."""

    __tablename__ = "auth_sessions"
    __table_args__ = (Index("ix_auth_sessions_user_id", "user_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_id)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    refresh_token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)  # CHAR(64)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship(back_populates="sessions")


class PrivacySettings(Base):
    """Tùy chọn cá nhân hóa; tạo khi đăng ký."""

    __tablename__ = "privacy_settings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    personalization_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped[User] = relationship(back_populates="privacy_settings")


class EmailTokenPurpose(str, Enum):
    VERIFY_EMAIL = "verify_email"
    RESET_PASSWORD = "reset_password"


class EmailToken(Base, CreatedAtMixin):
    """Token dùng một lần gửi qua email (xác minh email, đặt lại mật khẩu). DB chỉ lưu SHA-256."""

    __tablename__ = "email_tokens"
    __table_args__ = (
        CheckConstraint("purpose IN ('verify_email','reset_password')", name="ck_email_tokens_purpose"),
        Index("ix_email_tokens_user_purpose", "user_id", "purpose", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_id)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    purpose: Mapped[str] = mapped_column(Text, nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
