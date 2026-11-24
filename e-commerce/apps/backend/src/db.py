"""Cấu hình SQLAlchemy dùng chung cho mọi module.

Quy ước (xem docs/Database_Tables.md):
- id là UUID do app sinh (UUIDv7 nếu có, mặc định uuid4), không dùng default của DB.
- Thời gian là TIMESTAMPTZ (UTC).
"""
import os
import uuid
from datetime import datetime

from sqlalchemy import DateTime, create_engine, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://ecommerce:ecommerce@localhost:5432/ecommerce",
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def new_id() -> uuid.UUID:
    return getattr(uuid, "uuid7", uuid.uuid4)()


class Base(DeclarativeBase):
    pass


class CreatedAtMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class TimestampMixin(CreatedAtMixin):
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
