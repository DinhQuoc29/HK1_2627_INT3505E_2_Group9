"""Cấu hình SQLAlchemy dùng chung cho mọi module.

Quy ước (xem docs/Database_Tables.md):
- id là UUID do app sinh (UUIDv7 nếu có, mặc định uuid4), không dùng default của DB.
- Thời gian là TIMESTAMPTZ (UTC).
"""
import os
import uuid
from contextlib import contextmanager
from datetime import datetime

from dotenv import find_dotenv, load_dotenv

from sqlalchemy import DateTime, create_engine, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

load_dotenv(find_dotenv())  # đọc e-commerce/.env nếu có; biến môi trường thật được ưu tiên

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


@contextmanager
def session_scope():
    """Unit of work cho một request: service chỉ flush, commit một lần ở đây.

    Exception có thuộc tính `persist = True` vẫn commit trước khi lan ra ngoài
    (dùng để lưu bộ đếm đăng nhập sai rồi mới trả 401).
    """
    session = SessionLocal()
    try:
        yield session
    except BaseException as exc:
        if getattr(exc, "persist", False):
            session.commit()
        else:
            session.rollback()
        raise
    else:
        session.commit()
    finally:
        session.close()
