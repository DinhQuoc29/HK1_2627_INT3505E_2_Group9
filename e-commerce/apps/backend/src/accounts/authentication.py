"""Xác thực: băm mật khẩu, refresh token, access token (JWT), xác minh Google, guard login_required."""
import hashlib
import secrets
import uuid
from functools import wraps

import bcrypt
from flask import current_app, g
from flask_jwt_extended import create_access_token, get_jwt, verify_jwt_in_request

from accounts import repository
from common.errors import ProblemError
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


def issue_access_token(user_id: uuid.UUID, sid: uuid.UUID) -> str:
    return create_access_token(identity=str(user_id), additional_claims={"sid": str(sid)})


class GoogleUnavailable(Exception):
    """Không liên lạc được dịch vụ Google (lỗi tạm thời, nên thử lại)."""


def verify_google_id_token(credential: str) -> dict:
    """Xác minh ID token của Google; trả claims (sub, email, email_verified, name).

    ValueError: token sai. GoogleUnavailable: Google/ mạng không phản hồi.
    """
    from google.auth import exceptions as g_exc
    from google.auth.transport import requests as g_requests
    from google.oauth2 import id_token

    client_id = current_app.config["GOOGLE_CLIENT_ID"]
    if not client_id:
        raise GoogleUnavailable("GOOGLE_CLIENT_ID chưa được cấu hình")
    try:
        return id_token.verify_oauth2_token(credential, g_requests.Request(), client_id)
    except g_exc.TransportError as exc:
        raise GoogleUnavailable(str(exc)) from exc


def login_required(fn):
    """Yêu cầu access token hợp lệ VÀ phiên (sid) còn hiệu lực trong DB (logout có hiệu lực ngay)."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        try:
            sid = uuid.UUID(claims.get("sid", ""))
        except ValueError:
            raise ProblemError(401, "invalid-token", "Token không hợp lệ.")
        with session_scope() as s:
            row = repository.get_active_session_with_user(s, sid, utcnow())
        if row is None:
            raise ProblemError(401, "session-ended", "Phiên đăng nhập đã kết thúc, vui lòng đăng nhập lại.")
        g.current_session, g.current_user = row
        return fn(*args, **kwargs)

    return wrapper
