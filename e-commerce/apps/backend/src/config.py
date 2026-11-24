"""Cấu hình đọc từ biến môi trường (12-factor). Không có secret mặc định."""
import os
from datetime import timedelta


class Config:
    def __init__(self):
        self.JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
        self.JWT_ALGORITHM = "HS256"
        self.JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=int(os.getenv("ACCESS_TOKEN_MINUTES", "15")))
        self.JWT_TOKEN_LOCATION = ["headers"]
        # Refresh token (opaque) sống trong auth_sessions và cookie HttpOnly.
        self.REFRESH_TOKEN_DAYS = int(os.getenv("REFRESH_TOKEN_DAYS", "30"))
        self.REFRESH_COOKIE_NAME = "refresh_token"
        self.REFRESH_COOKIE_PATH = "/api/v1/auth"
        self.COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"
        # Khóa đăng nhập: sai LOGIN_MAX_FAILURES lần liên tiếp thì khóa LOGIN_LOCK_MINUTES phút.
        self.LOGIN_MAX_FAILURES = int(os.getenv("LOGIN_MAX_FAILURES", "5"))
        self.LOGIN_LOCK_MINUTES = int(os.getenv("LOGIN_LOCK_MINUTES", "15"))
        self.GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")

    def validate(self):
        if len(self.JWT_SECRET_KEY) < 32:
            raise RuntimeError(
                "JWT_SECRET_KEY phải có ít nhất 32 ký tự. Sinh bằng: "
                "python -c \"import secrets; print(secrets.token_urlsafe(48))\""
            )
