"""Phân quyền (RBAC). Dùng làm dependency sau xác thực: `Depends(require_role("admin"))`."""
from fastapi import Depends

from accounts.authentication import CurrentAuth, current_auth
from common.errors import ProblemError


def require_role(*roles: str):
    def checker(auth: CurrentAuth = Depends(current_auth)) -> CurrentAuth:
        if auth.user.role not in roles:
            raise ProblemError(403, "forbidden", "Bạn không có quyền thực hiện thao tác này.")
        return auth

    return checker
