"""Phân quyền (RBAC). Dùng sau login_required: @login_required @require_role('admin')."""
from functools import wraps

from flask import g

from common.errors import ProblemError


def require_role(*roles: str):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if g.current_user.role not in roles:
                raise ProblemError(403, "forbidden", "Bạn không có quyền thực hiện thao tác này.")
            return fn(*args, **kwargs)

        return wrapper

    return decorator
