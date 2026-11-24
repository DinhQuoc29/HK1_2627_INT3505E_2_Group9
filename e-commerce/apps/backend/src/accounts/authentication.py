"""Xác thực: băm mật khẩu, refresh token, access token (JWT), xác minh Google, dependency đăng nhập."""
import hashlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import timedelta

import bcrypt
import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from accounts import repository
from accounts.model import AuthSession, User
from common.errors import ProblemError
from config import Settings
from db import session_scope
from time_utils import utcnow

# Hash giả để thời gian phản hồi khi email không tồn tại gần giống khi sai mật khẩu.
_DUMMY_HASH = bcrypt.hashpw(b"dummy-password-for-timing", bcrypt.gensalt())


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("ascii")


def verify_password(password: str, stored_hash: str | None) -> bool:
    if not stored_hash:
        bcrypt.checkpw(password.encode("utf-8"), _DUMMY_HASH)
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("ascii"))
    except ValueError:
        return False


def new_refresh_token() -> tuple[str, str]:
    """Trả (token gốc gửi cho client, SHA-256 hex để lưu DB). Không lưu token gốc."""
    token = secrets.token_urlsafe(48)
    return token, hash_token(token)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def issue_access_token(st: Settings, user_id: uuid.UUID, sid: uuid.UUID) -> str:
    now = utcnow()
    claims = {
        "sub": str(user_id),
        "sid": str(sid),
        "jti": uuid.uuid4().hex,
        "iat": now,
        "exp": now + timedelta(minutes=st.access_token_minutes),
    }
    return jwt.encode(claims, st.jwt_secret_key, algorithm=st.jwt_algorithm)


class GoogleUnavailable(Exception):
    """Không liên lạc được dịch vụ Google (lỗi tạm thời, nên thử lại)."""


def verify_google_id_token(credential: str, client_id: str) -> dict:
    """Xác minh ID token của Google; trả claims (sub, email, email_verified, name).

    ValueError: token sai. GoogleUnavailable: Google/mạng không phản hồi hoặc chưa cấu hình client id.
    """
    from google.auth import exceptions as g_exc
    from google.auth.transport import requests as g_requests
    from google.oauth2 import id_token

    if not client_id:
        raise GoogleUnavailable("GOOGLE_CLIENT_ID chưa được cấu hình")
    try:
        return id_token.verify_oauth2_token(credential, g_requests.Request(), client_id)
    except g_exc.TransportError as exc:
        raise GoogleUnavailable(str(exc)) from exc


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


@dataclass
class CurrentAuth:
    user: User
    session: AuthSession


_bearer = HTTPBearer(auto_error=False)


def current_auth(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    st: Settings = Depends(get_settings),
) -> CurrentAuth:
    """Yêu cầu access token hợp lệ VÀ phiên (sid) còn hiệu lực trong DB (logout có hiệu lực ngay)."""
    if creds is None:
        raise ProblemError(401, "missing-token", "Cần đăng nhập.", headers={"WWW-Authenticate": "Bearer"})
    try:
        claims = jwt.decode(
            creds.credentials, st.jwt_secret_key, algorithms=[st.jwt_algorithm],
            options={"require": ["exp", "sub", "sid"]},
        )
        sid = uuid.UUID(claims["sid"])
    except jwt.ExpiredSignatureError:
        raise ProblemError(401, "token-expired", "Access token đã hết hạn.")
    except (jwt.InvalidTokenError, ValueError):
        raise ProblemError(401, "invalid-token", "Token không hợp lệ.")
    with session_scope() as s:
        row = repository.get_active_session_with_user(s, sid, utcnow())
    if row is None:
        raise ProblemError(401, "session-ended", "Phiên đăng nhập đã kết thúc, vui lòng đăng nhập lại.")
    session, user = row
    return CurrentAuth(user=user, session=session)
