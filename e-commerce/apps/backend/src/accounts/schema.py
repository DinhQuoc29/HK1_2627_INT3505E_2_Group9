"""Schema (Pydantic) cho request/response của Accounts. Field nhạy cảm không bao giờ ra API."""
import re
import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, StrictBool, field_validator

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _normalize_email(value):
    if not isinstance(value, str):
        raise ValueError("Email không hợp lệ.")
    value = value.strip().lower()
    if len(value) > 255 or not _EMAIL_RE.match(value):
        raise ValueError("Email không hợp lệ.")
    return value


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RegisterRequest(_Strict):
    email: str
    password: str
    full_name: str

    _email = field_validator("email", mode="before")(_normalize_email)

    @field_validator("password")
    @classmethod
    def _password_rules(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Mật khẩu tối thiểu 8 ký tự.")
        if len(v.encode("utf-8")) > 72:  # giới hạn của bcrypt
            raise ValueError("Mật khẩu tối đa 72 byte.")
        if not (any(c.isalpha() for c in v) and any(c.isdigit() for c in v)):
            raise ValueError("Mật khẩu cần có cả chữ và số.")
        return v

    @field_validator("full_name", mode="before")
    @classmethod
    def _name(cls, v):
        if not isinstance(v, str):
            raise ValueError("Họ tên không hợp lệ.")
        v = v.strip()
        if not 1 <= len(v) <= 100:
            raise ValueError("Họ tên từ 1 đến 100 ký tự.")
        return v


class LoginRequest(_Strict):
    email: str
    password: str

    _email = field_validator("email", mode="before")(_normalize_email)

    @field_validator("password")
    @classmethod
    def _password_present(cls, v: str) -> str:
        if not 1 <= len(v) <= 128:
            raise ValueError("Vui lòng nhập mật khẩu.")
        return v


class GoogleLoginRequest(_Strict):
    credential: str

    @field_validator("credential")
    @classmethod
    def _credential(cls, v: str) -> str:
        if not 1 <= len(v) <= 4096:
            raise ValueError("Credential không hợp lệ.")
        return v


class FacebookLoginRequest(_Strict):
    access_token: str

    @field_validator("access_token")
    @classmethod
    def _token(cls, v: str) -> str:
        if not 1 <= len(v) <= 4096:
            raise ValueError("Access token không hợp lệ.")
        return v


class LinkIdentityRequest(_Strict):
    provider: Literal["google", "facebook"]
    credential: str  # Google: ID token; Facebook: access token

    @field_validator("credential")
    @classmethod
    def _credential(cls, v: str) -> str:
        if not 1 <= len(v) <= 4096:
            raise ValueError("Credential không hợp lệ.")
        return v


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str
    role: str
    created_at: datetime
    providers: list[str] = []  # nhà cung cấp OAuth đã liên kết, ví dụ ["google", "facebook"]
    has_password: bool = True  # False: tài khoản chỉ đăng nhập bằng Google
    email_verified: bool = False


class AuthSessionOut(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: UserOut


def _check_new_password(v: str) -> str:
    if len(v) < 8:
        raise ValueError("Mật khẩu tối thiểu 8 ký tự.")
    if len(v.encode("utf-8")) > 72:
        raise ValueError("Mật khẩu tối đa 72 byte.")
    if not (any(c.isalpha() for c in v) and any(c.isdigit() for c in v)):
        raise ValueError("Mật khẩu cần có cả chữ và số.")
    return v


class ChangePasswordRequest(_Strict):
    current_password: str | None = None  # bỏ trống nếu tài khoản chưa có mật khẩu (chỉ đăng nhập Google/Facebook)
    new_password: str

    _new = field_validator("new_password")(_check_new_password)


class AdminUserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str
    role: str
    status: str
    created_at: datetime
    has_shop: bool = False


class AdminUserPage(BaseModel):
    items: list[AdminUserOut]
    next_cursor: str | None = None


class AdminUpdateUserRequest(_Strict):
    role: Literal["buyer", "admin"] | None = None  # seller chỉ có được bằng cách mở shop
    status: Literal["active", "suspended"] | None = None


class ForgotPasswordRequest(_Strict):
    email: str

    _email = field_validator("email", mode="before")(_normalize_email)


class TokenRequest(_Strict):
    token: str

    @field_validator("token")
    @classmethod
    def _token(cls, v: str) -> str:
        if not 20 <= len(v) <= 200:
            raise ValueError("Token không hợp lệ.")
        return v


class ResetPasswordRequest(TokenRequest):
    new_password: str

    _new = field_validator("new_password")(_check_new_password)


class PrivacyPreference(_Strict):
    personalization_enabled: StrictBool
