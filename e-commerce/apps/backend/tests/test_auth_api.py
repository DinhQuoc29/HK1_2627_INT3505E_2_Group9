import re
import uuid

import pytest
from sqlalchemy import text

import accounts.authentication as auth_mod
from app import create_app
from db import engine

PW = "Matkhau123"


@pytest.fixture(scope="module")
def app():
    return create_app({"TESTING": True, "LOGIN_MAX_FAILURES": 3, "GOOGLE_CLIENT_ID": "test-client"})


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture(scope="module", autouse=True)
def _cleanup():
    yield
    with engine.begin() as c:
        c.execute(text("delete from users where email like '%@authtest.local'"))


def _email():
    return f"u{uuid.uuid4().hex[:10]}@authtest.local"


def _register(client, email=None, password=PW, name="Nguyen Van A"):
    email = email or _email()
    r = client.post("/api/v1/users", json={"email": email, "password": password, "full_name": name})
    return email, r


def _bearer(r):
    return {"Authorization": f"Bearer {r.get_json()['access_token']}"}


def test_register_returns_session_and_hides_secrets(client):
    email, r = _register(client)
    assert r.status_code == 201
    body = r.get_json()
    assert body["user"]["email"] == email and body["user"]["role"] == "buyer"
    assert "password" not in str(body) and "password_hash" not in str(body)
    cookie = r.headers["Set-Cookie"]
    assert "refresh_token=" in cookie and "HttpOnly" in cookie and "SameSite=Lax" in cookie
    assert "Path=/api/v1/auth" in cookie


def test_register_stores_bcrypt_hash_and_privacy_settings(client):
    email, _ = _register(client)
    with engine.connect() as c:
        row = c.execute(text(
            "select u.password_hash, p.personalization_enabled from users u "
            "join privacy_settings p on p.user_id=u.id where u.email=:e"), {"e": email}).one()
    assert row.password_hash.startswith("$2") and PW not in row.password_hash
    assert row.personalization_enabled is True


def test_register_duplicate_email_is_409_problem_json(client):
    email, _ = _register(client)
    _, r = _register(client, email=email.upper())
    assert r.status_code == 409
    assert r.mimetype == "application/problem+json"
    assert r.get_json()["type"] == "/problems/email-already-registered"


@pytest.mark.parametrize("payload,field", [
    ({"email": "khong-phai-email", "password": PW, "full_name": "A"}, "email"),
    ({"email": "a@authtest.local", "password": "short1", "full_name": "A"}, "password"),
    ({"email": "a@authtest.local", "password": "chiCoChu", "full_name": "A"}, "password"),
    ({"email": "a@authtest.local", "password": PW, "full_name": "  "}, "full_name"),
    ({"email": "a@authtest.local", "password": PW}, "full_name"),
])
def test_register_validation_422(client, payload, field):
    r = client.post("/api/v1/users", json=payload)
    assert r.status_code == 422
    assert field in [e["field"] for e in r.get_json()["errors"]]


def test_malformed_json_is_400(client):
    r = client.post("/api/v1/users", data="{oops", content_type="application/json")
    assert r.status_code == 400 and r.mimetype == "application/problem+json"


def test_login_success_and_me(client):
    email, _ = _register(client)
    r = client.post("/api/v1/auth/sessions", json={"email": email, "password": PW})
    assert r.status_code == 201
    me = client.get("/api/v1/users/me", headers=_bearer(r))
    assert me.status_code == 200 and me.get_json()["email"] == email


def test_login_wrong_password_and_unknown_email_look_the_same(client):
    email, _ = _register(client)
    a = client.post("/api/v1/auth/sessions", json={"email": email, "password": "Sai12345"})
    b = client.post("/api/v1/auth/sessions", json={"email": _email(), "password": "Sai12345"})
    assert a.status_code == b.status_code == 401
    assert a.get_json()["detail"] == b.get_json()["detail"]


def test_account_locks_after_repeated_failures_even_with_right_password(client):
    email, _ = _register(client)
    for _ in range(3):
        assert client.post("/api/v1/auth/sessions", json={"email": email, "password": "Sai12345"}).status_code == 401
    r = client.post("/api/v1/auth/sessions", json={"email": email, "password": PW})
    assert r.status_code == 429 and int(r.headers["Retry-After"]) > 0


def test_protected_endpoint_requires_token(client):
    r = client.get("/api/v1/users/me")
    assert r.status_code == 401 and r.mimetype == "application/problem+json"
    r = client.get("/api/v1/users/me", headers={"Authorization": "Bearer nonsense"})
    assert r.status_code == 401


def test_logout_ends_session_immediately(client):
    email, reg = _register(client)
    headers = _bearer(reg)
    assert client.get("/api/v1/users/me", headers=headers).status_code == 200
    assert client.delete("/api/v1/auth/sessions/current", headers=headers).status_code == 204
    assert client.get("/api/v1/users/me", headers=headers).status_code == 401  # access token cũ bị từ chối ngay
    assert client.post("/api/v1/auth/tokens").status_code == 401  # cookie refresh đã bị xóa/thu hồi


def test_refresh_rotates_token_and_rejects_reuse(app):
    c = app.test_client()
    _, reg = _register(c)
    old_cookie = re.search(r"refresh_token=([^;]+)", reg.headers["Set-Cookie"]).group(1)
    r = c.post("/api/v1/auth/tokens")
    assert r.status_code == 200 and "access_token" in r.get_json()
    new_cookie = re.search(r"refresh_token=([^;]+)", r.headers["Set-Cookie"]).group(1)
    assert new_cookie != old_cookie
    stale = app.test_client()
    stale.set_cookie("refresh_token", old_cookie, path="/api/v1/auth")
    assert stale.post("/api/v1/auth/tokens").status_code == 401


def test_role_guard_forbids_buyer():
    from flask import Blueprint
    from accounts.authentication import login_required
    from accounts.permissions import require_role

    app = create_app({"TESTING": True})
    bp = Blueprint("admin_probe", __name__)

    @bp.get("/_admin-probe")
    @login_required
    @require_role("admin")
    def probe():
        return "ok"

    app.register_blueprint(bp)
    client = app.test_client()
    _, reg = _register(client)
    assert client.get("/_admin-probe", headers=_bearer(reg)).status_code == 403


def _fake_google(monkeypatch, **claims):
    base = {"sub": uuid.uuid4().hex, "email": _email(), "email_verified": True, "name": "Gg User"}
    base.update(claims)
    monkeypatch.setattr(auth_mod, "verify_google_id_token", lambda cred: base)
    return base


def test_google_creates_user_without_password_then_returns_same_account(client, monkeypatch):
    claims = _fake_google(monkeypatch)
    r1 = client.post("/api/v1/auth/sessions/google", json={"credential": "x"})
    r2 = client.post("/api/v1/auth/sessions/google", json={"credential": "x"})
    assert r1.status_code == r2.status_code == 201
    assert r1.get_json()["user"]["id"] == r2.get_json()["user"]["id"]
    with engine.connect() as c:
        pw = c.execute(text("select password_hash from users where email=:e"), {"e": claims["email"]}).scalar_one()
    assert pw is None
    # tài khoản chỉ-Google không đăng nhập được bằng mật khẩu
    assert client.post("/api/v1/auth/sessions", json={"email": claims["email"], "password": PW}).status_code == 401


def test_google_links_existing_password_account(client, monkeypatch):
    email, reg = _register(client)
    _fake_google(monkeypatch, email=email)
    r = client.post("/api/v1/auth/sessions/google", json={"credential": "x"})
    assert r.status_code == 201 and r.get_json()["user"]["id"] == reg.get_json()["user"]["id"]


def test_google_unverified_email_rejected(client, monkeypatch):
    _fake_google(monkeypatch, email_verified=False)
    assert client.post("/api/v1/auth/sessions/google", json={"credential": "x"}).status_code == 401


def test_google_outage_is_503_and_creates_nothing(client, monkeypatch):
    def boom(_):
        raise auth_mod.GoogleUnavailable("down")
    monkeypatch.setattr(auth_mod, "verify_google_id_token", boom)
    with engine.connect() as c:
        before = c.execute(text("select count(*) from users")).scalar_one()
    r = client.post("/api/v1/auth/sessions/google", json={"credential": "x"})
    assert r.status_code == 503 and "Retry-After" in r.headers
    assert "Set-Cookie" not in r.headers
    with engine.connect() as c:
        assert c.execute(text("select count(*) from users")).scalar_one() == before
