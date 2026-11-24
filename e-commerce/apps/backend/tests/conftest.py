import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

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
