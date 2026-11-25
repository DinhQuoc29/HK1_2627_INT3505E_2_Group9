"""Tùy chọn cá nhân hóa theo tài khoản, đọc trực tiếp từ cơ sở dữ liệu."""
import uuid

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from accounts.model import PrivacySettings


def personalization_enabled(s: Session, user_id: uuid.UUID) -> bool:
    stored = s.scalar(select(PrivacySettings.personalization_enabled).where(PrivacySettings.user_id == user_id))
    # Tài khoản cũ chưa có dòng cài đặt dùng mặc định của schema.
    return True if stored is None else stored


def set_personalization(s: Session, user_id: uuid.UUID, enabled: bool) -> None:
    stmt = insert(PrivacySettings).values(user_id=user_id, personalization_enabled=enabled)
    s.execute(stmt.on_conflict_do_update(
        index_elements=[PrivacySettings.user_id],
        set_={"personalization_enabled": stmt.excluded.personalization_enabled, "updated_at": func.now()},
        where=PrivacySettings.personalization_enabled != stmt.excluded.personalization_enabled,
    ))
