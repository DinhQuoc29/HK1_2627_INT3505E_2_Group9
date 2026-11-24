"""Endpoint Accounts (/api/v1). Danh từ số nhiều, kebab-case; lỗi trả problem+json."""
from fastapi import APIRouter, Depends, Request, Response

from accounts import service
from accounts.authentication import CurrentAuth, current_auth, get_settings
from accounts.schema import AuthSessionOut, GoogleLoginRequest, LoginRequest, RegisterRequest, UserOut
from common.errors import ProblemError, problem_response
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
        user=UserOut.model_validate(issued.user),
    )


@router.post("/users", status_code=201, response_model=AuthSessionOut)
def register_user(body: RegisterRequest, response: Response, st: Settings = Depends(get_settings)):
    with session_scope() as s:
        issued = service.register(s, st, body.email, body.password, body.full_name)
    return _auth_payload(issued, st, response, 201)


@router.get("/users/me", response_model=UserOut)
def get_me(response: Response, auth: CurrentAuth = Depends(current_auth)):
    response.headers["Cache-Control"] = "no-store"
    return auth.user


@router.post("/auth/sessions", status_code=201, response_model=AuthSessionOut)
def create_session(body: LoginRequest, response: Response, st: Settings = Depends(get_settings)):
    with session_scope() as s:
        issued = service.login(s, st, body.email, body.password)
    return _auth_payload(issued, st, response, 201)


@router.post("/auth/sessions/google", status_code=201, response_model=AuthSessionOut)
def create_google_session(body: GoogleLoginRequest, response: Response, st: Settings = Depends(get_settings)):
    with session_scope() as s:
        issued = service.login_with_google(s, st, body.credential)
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
