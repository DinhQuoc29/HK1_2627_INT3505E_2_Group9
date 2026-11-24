import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest

from db import Base, SessionLocal, engine

import orders.model  # noqa: F401
import orders.payments.model  # noqa: F401
import reviews.model  # noqa: F401


@pytest.fixture(scope="session", autouse=True)
def _reflect_foreign_tables():
    """Nạp các bảng thuộc module khác (users, shops, products...) từ DB.

    Bỏ fixture này khi các model tương ứng (accounts, catalog) đã được import.
    """
    missing = [t for t in ("users", "shops", "products") if t not in Base.metadata.tables]
    if missing:
        Base.metadata.reflect(bind=engine, only=missing)


@pytest.fixture
def session():
    s = SessionLocal()
    try:
        yield s
    finally:
        s.rollback()
        s.close()
