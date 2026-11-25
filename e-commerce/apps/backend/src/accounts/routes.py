"""Endpoint Accounts (/api/v1). Danh từ số nhiều, kebab-case; lỗi trả problem+json."""
import uuid
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request, Response

from accounts import admin, emails, service
from accounts.permissions import require_role
from accounts.authentication import CurrentAuth, current_auth, get_settings
from accounts.schema import (
    AdminUpdateUserRequest, AdminUserOut, AdminUserPage, AuthSessionOut, ChangePasswordRequest, FacebookLoginRequest, ForgotPasswordRequest, ResetPasswordRequest, TokenRequest, GoogleLoginRequest, LinkIdentityRequest, LoginRequest, RegisterRequest,
    UserOut,
)
from common.errors import ProblemError, problem_response
from common.ratelimit import rate_limited
from config import Settings
from db import session_scope

router = APIRouter(prefix="/api/v1")


def _auth_payload(issued: service.IssuedSession, st: Settings, response: Response, status: int) -> AuthSessionOut:
    response.status_code = status
    response.set_cookie(
        st.refresh_cookie_name, issued.refresh_token,
        max_age=st.refresh_token_days * 86400, httponly=True,
        secure=st.cookie_secure, samesite="lax", path=st.refresh_cookie_path,
    )
    response.headers["Cache-Control"] = "no-store"
    return AuthSessionOut(
        access_token=issued.access_token,
        expires_in=st.access_token_minutes * 60,
        user=issued.user,
    )


@router.post("/users", status_code=201, response_model=AuthSessionOut, dependencies=[Depends(rate_limited("auth"))])
def register_user(body: RegisterRequest, response: Response, tasks: BackgroundTasks, request: Request,
                  st: Settings = Depends(get_settings)):
    with session_scope() as s:
        issued = service.register(s, st, body.email, body.password, body.full_name)
    if issued.verify_token:
        tasks.add_task(request.app.state.mailer.send,
                       emails.verification_email(st, issued.user.email, issued.user.full_name, issued.verify_token))
    return _auth_payload(issued, st, response, 201)


@router.get("/users/me", response_model=UserOut)
def get_me(response: Response, auth: CurrentAuth = Depends(current_auth)):
    response.headers["Cache-Control"] = "no-store"
    with session_scope() as s:
        return service.profile(s, auth.user)


@router.post("/users/me/identities", status_code=201, response_model=UserOut)
def link_identity(body: LinkIdentityRequest, response: Response, auth: CurrentAuth = Depends(current_auth),
                  st: Settings = Depends(get_settings)):
    """Liên kết tài khoản Google/Facebook với người dùng đang đăng nhập; trả hồ sơ đã cập nhật."""
    with session_scope() as s:
        profile = service.link_identity(s, st, auth.user, body.provider, body.credential)
    response.headers["Cache-Control"] = "no-store"
    return profile


@router.delete("/users/me/identities/{provider}", status_code=204)
def unlink_identity(provider: str, auth: CurrentAuth = Depends(current_auth)):
    if provider not in ("google", "facebook"):
        raise ProblemError(404, "identity-not-found", "Nhà cung cấp không được hỗ trợ.")
    with session_scope() as s:
        service.unlink_provider(s, auth.user, provider)
    return Response(status_code=204)


@router.post("/auth/sessions", status_code=201, response_model=AuthSessionOut, dependencies=[Depends(rate_limited("auth"))])
def create_session(body: LoginRequest, response: Response, st: Settings = Depends(get_settings)):
    with session_scope() as s:
        issued = service.login(s, st, body.email, body.password)
    return _auth_payload(issued, st, response, 201)


@router.post("/auth/sessions/google", status_code=201, response_model=AuthSessionOut, dependencies=[Depends(rate_limited("auth"))])
def create_google_session(body: GoogleLoginRequest, response: Response, st: Settings = Depends(get_settings)):
    with session_scope() as s:
        issued = service.login_with_google(s, st, body.credential)
    return _auth_payload(issued, st, response, 201)


@router.post("/auth/sessions/facebook", status_code=201, response_model=AuthSessionOut, dependencies=[Depends(rate_limited("auth"))])
def create_facebook_session(body: FacebookLoginRequest, response: Response, st: Settings = Depends(get_settings)):
    with session_scope() as s:
        issued = service.login_with_facebook(s, st, body.access_token)
    return _auth_payload(issued, st, response, 201)


@router.delete("/auth/sessions/current", status_code=204)
def delete_current_session(auth: CurrentAuth = Depends(current_auth), st: Settings = Depends(get_settings)):
    with session_scope() as s:
        service.logout(s, auth.session.id)
    resp = Response(status_code=204)
    resp.delete_cookie(st.refresh_cookie_name, path=st.refresh_cookie_path)
    return resp


@router.post("/auth/tokens", response_model=AuthSessionOut)
def refresh_access_token(request: Request, response: Response, st: Settings = Depends(get_settings)):
    """Đổi refresh token (cookie HttpOnly) lấy access token mới; refresh token được xoay vòng."""
    try:
        with session_scope() as s:
            issued = service.refresh(s, st, request.cookies.get(st.refresh_cookie_name))
    except ProblemError as exc:
        err = problem_response(exc, request)
        err.delete_cookie(st.refresh_cookie_name, path=st.refresh_cookie_path)
        return err
    return _auth_payload(issued, st, response, 200)


@router.put("/users/me/password", status_code=204)
def change_password(body: ChangePasswordRequest, auth: CurrentAuth = Depends(current_auth)):
    """Đổi mật khẩu (hoặc đặt mật khẩu lần đầu cho tài khoản social); các phiên khác bị đăng xuất."""
    with session_scope() as s:
        service.change_password(s, auth.user, auth.session.id, body.current_password, body.new_password)
    return Response(status_code=204)


@router.get("/admin/users", response_model=AdminUserPage)
def admin_list_users(
    response: Response,
    role: Literal["buyer", "seller", "admin"] | None = None,
    status: Literal["active", "suspended"] | None = None,
    q: str | None = Query(None, max_length=100),
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = Query(None, max_length=200),
    _: CurrentAuth = Depends(require_role("admin")),
):
    response.headers["Cache-Control"] = "no-store"
    with session_scope() as s:
        return admin.list_users(s, role=role, status=status, q=q, limit=limit, cursor=cursor)


@router.get("/admin/users/{user_id}", response_model=AdminUserOut)
def admin_get_user(user_id: uuid.UUID, _: CurrentAuth = Depends(require_role("admin"))):
    with session_scope() as s:
        return admin.get_user(s, user_id)


@router.patch("/admin/users/{user_id}", response_model=AdminUserOut)
def admin_update_user(user_id: uuid.UUID, body: AdminUpdateUserRequest, auth: CurrentAuth = Depends(require_role("admin"))):
    """Khóa/mở khóa tài khoản hoặc cấp/thu quyền admin. Không áp dụng cho chính mình."""
    with session_scope() as s:
        return admin.update_user(s, auth.user, user_id, body.role, body.status)


@router.post("/auth/email-verifications", status_code=202, dependencies=[Depends(rate_limited("auth"))])
def resend_email_verification(tasks: BackgroundTasks, request: Request, auth: CurrentAuth = Depends(current_auth),
                              st: Settings = Depends(get_settings)):
    """Gửi lại email xác minh cho người đang đăng nhập (cách nhau tối thiểu vài chục giây)."""
    with session_scope() as s:
        token = service.request_email_verification(s, st, auth.user)
    tasks.add_task(request.app.state.mailer.send,
                   emails.verification_email(st, auth.user.email, auth.user.full_name, token))
    return {"status": "sent"}


@router.post("/auth/email-verifications/confirmation", status_code=204, dependencies=[Depends(rate_limited("auth"))])
def confirm_email_verification(body: TokenRequest):
    with session_scope() as s:
        service.confirm_email(s, body.token)
    return Response(status_code=204)


@router.post("/auth/password-resets", status_code=202, dependencies=[Depends(rate_limited("auth"))])
def request_password_reset(body: ForgotPasswordRequest, tasks: BackgroundTasks, request: Request,
                           st: Settings = Depends(get_settings)):
    """Luôn trả 202 dù email có tồn tại hay không (không lộ danh sách tài khoản)."""
    with session_scope() as s:
        found = service.request_password_reset(s, st, body.email)
    if found:
        user, token = found
        tasks.add_task(request.app.state.mailer.send, emails.reset_password_email(st, user.email, user.full_name, token))
    return {"status": "accepted"}


@router.post("/auth/password-resets/confirmation", status_code=204, dependencies=[Depends(rate_limited("auth"))])
def confirm_password_reset(body: ResetPasswordRequest):
    with session_scope() as s:
        service.confirm_password_reset(s, body.token, body.new_password)
    return Response(status_code=204)
