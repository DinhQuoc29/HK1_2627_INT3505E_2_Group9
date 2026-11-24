"""Tạo tài khoản buyer mẫu cho môi trường phát triển (chạy lại nhiều lần vẫn an toàn).

    cd apps/backend && .venv/bin/python scripts/seed_dev_user.py

Chỉ dùng với DB local. Đây là tài khoản demo, KHÔNG dùng cho môi trường thật.
"""
import pathlib
import sys
from urllib.parse import urlparse

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

import accounts.model  # noqa: E402,F401
from accounts import authentication, repository  # noqa: E402
from accounts.model import Role, User  # noqa: E402
from db import DATABASE_URL, new_id, session_scope  # noqa: E402

DEV_EMAIL = "demo.buyer@example.com"
DEV_PASSWORD = "Demo12345"
DEV_NAME = "Người Mua Demo"


def main() -> None:
    host = urlparse(DATABASE_URL.replace("postgresql+psycopg", "postgresql")).hostname
    if host not in ("localhost", "127.0.0.1", "::1"):
        sys.exit(f"Từ chối: DATABASE_URL trỏ tới {host!r}, script này chỉ dành cho DB local.")
    with session_scope() as s:
        if repository.get_user_by_email(s, DEV_EMAIL):
            print(f"Đã có tài khoản {DEV_EMAIL}, giữ nguyên.")
            return
        repository.add_user(
            s,
            User(id=new_id(), email=DEV_EMAIL, full_name=DEV_NAME,
                 password_hash=authentication.hash_password(DEV_PASSWORD), role=Role.BUYER.value),
        )
        print(f"Đã tạo tài khoản {DEV_EMAIL} (mật khẩu ở hằng DEV_PASSWORD trong file này).")


if __name__ == "__main__":
    main()
