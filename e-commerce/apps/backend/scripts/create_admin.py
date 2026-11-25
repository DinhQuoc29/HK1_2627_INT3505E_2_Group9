"""Tạo (hoặc nâng quyền) tài khoản admin. Admin không thể tự đăng ký qua API.

    cd apps/backend
    ADMIN_EMAIL=admin@example.com ADMIN_PASSWORD='Admin12345' ADMIN_NAME='Quản trị' \
        ../../.venv/bin/python scripts/create_admin.py

Email đã tồn tại: giữ mật khẩu, chỉ nâng vai trò lên admin (và mở khóa). Chạy lại nhiều lần vẫn an toàn.
"""
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

import accounts.model  # noqa: E402,F401
import catalog.model  # noqa: E402,F401
from accounts import authentication, repository  # noqa: E402
from accounts.model import Role, User, UserStatus  # noqa: E402
from accounts.schema import RegisterRequest  # noqa: E402
from db import new_id, session_scope  # noqa: E402


def main() -> None:
    email, password = os.getenv("ADMIN_EMAIL", ""), os.getenv("ADMIN_PASSWORD", "")
    name = os.getenv("ADMIN_NAME", "Quản trị viên")
    if not email or not password:
        sys.exit("Cần đặt biến môi trường ADMIN_EMAIL và ADMIN_PASSWORD.")
    try:  # dùng lại đúng quy tắc kiểm tra của API đăng ký
        data = RegisterRequest(email=email, password=password, full_name=name)
    except ValueError as exc:
        sys.exit(f"Dữ liệu không hợp lệ: {exc}")
    with session_scope() as s:
        user = repository.get_user_by_email(s, data.email)
        if user is None:
            repository.add_user(s, User(
                id=new_id(), email=data.email, full_name=data.full_name,
                password_hash=authentication.hash_password(data.password), role=Role.ADMIN.value,
            ))
            print(f"Đã tạo admin {data.email}.")
        else:
            repository.set_role(s, user, Role.ADMIN.value)
            repository.set_status(s, user, UserStatus.ACTIVE.value)
            print(f"Đã nâng {data.email} lên admin (giữ nguyên mật khẩu).")


if __name__ == "__main__":
    main()
