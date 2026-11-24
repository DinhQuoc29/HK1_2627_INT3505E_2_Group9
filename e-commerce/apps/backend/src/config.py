"""Cấu hình đọc từ biến môi trường (12-factor). Không có secret mặc định."""
import os
from dataclasses import dataclass, fields


@dataclass
class Settings:
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 15
    # Refresh token (opaque) sống trong auth_sessions và cookie HttpOnly.
    refresh_token_days: int = 30
    refresh_cookie_name: str = "refresh_token"
    refresh_cookie_path: str = "/api/v1/auth"
    cookie_secure: bool = False
    # Khóa đăng nhập: sai login_max_failures lần liên tiếp thì khóa login_lock_minutes phút.
    login_max_failures: int = 5
    login_lock_minutes: int = 15
    google_client_id: str = ""

    @classmethod
    def from_env(cls, **overrides) -> "Settings":
        e = os.getenv
        s = cls(
            jwt_secret_key=e("JWT_SECRET_KEY", ""),
            access_token_minutes=int(e("ACCESS_TOKEN_MINUTES", "15")),
            refresh_token_days=int(e("REFRESH_TOKEN_DAYS", "30")),
            cookie_secure=e("COOKIE_SECURE", "false").lower() == "true",
            login_max_failures=int(e("LOGIN_MAX_FAILURES", "5")),
            login_lock_minutes=int(e("LOGIN_LOCK_MINUTES", "15")),
            google_client_id=e("GOOGLE_CLIENT_ID", ""),
        )
        names = {f.name for f in fields(cls)}
        for k, v in overrides.items():
            if k not in names:
                raise KeyError(f"Cấu hình không tồn tại: {k}")
            setattr(s, k, v)
        return s

    def validate(self) -> None:
        if len(self.jwt_secret_key) < 32:
            raise RuntimeError(
                "JWT_SECRET_KEY phải có ít nhất 32 ký tự. Sinh bằng: "
                "python -c \"import secrets; print(secrets.token_urlsafe(48))\""
            )
