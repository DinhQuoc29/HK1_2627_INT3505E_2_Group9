"""Endpoint Accounts (/api/v1). Danh từ số nhiều, kebab-case; lỗi trả problem+json."""
from flask import Blueprint, current_app, g, jsonify, make_response, request

from accounts import service
from accounts.authentication import login_required
from accounts.schema import GoogleLoginSchema, LoginSchema, RegisterSchema, UserSchema, load_body
from common.errors import ProblemError
from db import session_scope

bp = Blueprint("accounts", __name__, url_prefix="/api/v1")


def _auth_response(issued, status):
    cfg = current_app.config
    resp = make_response(
        jsonify(
            access_token=issued.access_token,
            token_type="Bearer",
            expires_in=int(cfg["JWT_ACCESS_TOKEN_EXPIRES"].total_seconds()),
            user=UserSchema().dump(issued.user),
        ),
        status,
    )
    resp.set_cookie(
        cfg["REFRESH_COOKIE_NAME"], issued.refresh_token,
        max_age=cfg["REFRESH_TOKEN_DAYS"] * 86400, httponly=True,
        secure=cfg["COOKIE_SECURE"], samesite="Lax", path=cfg["REFRESH_COOKIE_PATH"],
    )
    resp.headers["Cache-Control"] = "no-store"
    return resp


def _json_body():
    data = request.get_json(silent=True)
    if data is None:
        raise ProblemError(400, "invalid-json", "Body phải là JSON hợp lệ (Content-Type: application/json).")
    return data


@bp.post("/users")
def register_user():
    data = load_body(RegisterSchema(), _json_body())
    with session_scope() as s:
        issued = service.register(s, **data)
    return _auth_response(issued, 201)


@bp.get("/users/me")
@login_required
def get_me():
    resp = jsonify(UserSchema().dump(g.current_user))
    resp.headers["Cache-Control"] = "no-store"
    return resp


@bp.post("/auth/sessions")
def create_session():
    data = load_body(LoginSchema(), _json_body())
    with session_scope() as s:
        issued = service.login(s, data["email"], data["password"])
    return _auth_response(issued, 201)


@bp.post("/auth/sessions/google")
def create_google_session():
    data = load_body(GoogleLoginSchema(), _json_body())
    with session_scope() as s:
        issued = service.login_with_google(s, data["credential"])
    return _auth_response(issued, 201)


@bp.delete("/auth/sessions/current")
@login_required
def delete_current_session():
    with session_scope() as s:
        service.logout(s, g.current_session.id)
    cfg = current_app.config
    resp = make_response("", 204)
    resp.delete_cookie(cfg["REFRESH_COOKIE_NAME"], path=cfg["REFRESH_COOKIE_PATH"])
    return resp


@bp.post("/auth/tokens")
def refresh_access_token():
    """Đổi refresh token (cookie HttpOnly) lấy access token mới; refresh token được xoay vòng."""
    cfg = current_app.config
    try:
        with session_scope() as s:
            issued = service.refresh(s, request.cookies.get(cfg["REFRESH_COOKIE_NAME"]))
    except ProblemError as exc:
        from common.errors import problem_response
        resp = problem_response(exc)
        resp.delete_cookie(cfg["REFRESH_COOKIE_NAME"], path=cfg["REFRESH_COOKIE_PATH"])
        return resp
    return _auth_response(issued, 200)
