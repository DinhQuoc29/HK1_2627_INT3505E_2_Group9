import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Test phải độc lập với .env của từng máy: biến môi trường thật được ưu tiên hơn .env (dotenv không ghi đè).
for _key, _value in {
    "GOOGLE_CLIENT_ID": "", "FACEBOOK_APP_ID": "", "FACEBOOK_APP_SECRET": "",
    "RATE_LIMIT_PER_MINUTE": "20", "LOGIN_MAX_FAILURES": "5",
}.items():
    os.environ[_key] = _value

import pytest

from db import SessionLocal

# Import toàn bộ entity để metadata đầy đủ.
import accounts.model  # noqa: F401
import cart.model  # noqa: F401
import catalog.model  # noqa: F401
import orders.model  # noqa: F401
import orders.payments.model  # noqa: F401
import reviews.model  # noqa: F401


@pytest.fixture
def session():
    s = SessionLocal()
    try:
        yield s
    finally:
        s.rollback()
        s.close()
