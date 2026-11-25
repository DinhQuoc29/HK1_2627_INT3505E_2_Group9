import re
import uuid

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import text

import accounts.authentication as auth_mod
from app import create_app
from db import engine

PW = "Matkhau123"


@pytest.fixture(scope="module")
def app():
    return create_app(login_max_failures=3, google_client_id="test-client", rate_limit_per_minute=0)


@pytest.fixture
def client(app):
    return TestClient(app)


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
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_register_returns_session_and_hides_secrets(client):
    email, r = _register(client)
    assert r.status_code == 201
    body = r.json()
    assert body["user"]["email"] == email and body["user"]["role"] == "buyer"
    assert "password" not in body["user"] and "password_hash" not in str(body)
    cookie = r.headers["set-cookie"].lower()
    assert "refresh_token=" in cookie and "httponly" in cookie and "samesite=lax" in cookie
    assert "path=/api/v1/auth" in cookie


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
    assert r.headers["content-type"].startswith("application/problem+json")
    assert r.json()["type"] == "/problems/email-already-registered"


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
    assert field in [e["field"] for e in r.json()["errors"]]


def test_malformed_json_is_400(client):
    r = client.post("/api/v1/users", content="{oops", headers={"Content-Type": "application/json"})
    assert r.status_code == 400 and r.headers["content-type"].startswith("application/problem+json")


def test_login_success_and_me(client):
    email, _ = _register(client)
    r = client.post("/api/v1/auth/sessions", json={"email": email, "password": PW})
    assert r.status_code == 201
    me = client.get("/api/v1/users/me", headers=_bearer(r))
    assert me.status_code == 200 and me.json()["email"] == email


def test_login_wrong_password_and_unknown_email_look_the_same(client):
    email, _ = _register(client)
    a = client.post("/api/v1/auth/sessions", json={"email": email, "password": "Sai12345"})
    b = client.post("/api/v1/auth/sessions", json={"email": _email(), "password": "Sai12345"})
    assert a.status_code == b.status_code == 401
    assert a.json()["detail"] == b.json()["detail"]


def test_account_locks_after_repeated_failures_even_with_right_password(client):
    email, _ = _register(client)
    for _ in range(3):
        assert client.post("/api/v1/auth/sessions", json={"email": email, "password": "Sai12345"}).status_code == 401
    r = client.post("/api/v1/auth/sessions", json={"email": email, "password": PW})
    assert r.status_code == 429 and int(r.headers["Retry-After"]) > 0


def test_protected_endpoint_requires_token(client):
    r = client.get("/api/v1/users/me")
    assert r.status_code == 401 and r.headers["content-type"].startswith("application/problem+json")
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
    c = TestClient(app)
    _, reg = _register(c)
    old_cookie = re.search(r"refresh_token=([^;]+)", reg.headers["set-cookie"]).group(1)
    r = c.post("/api/v1/auth/tokens")
    assert r.status_code == 200 and "access_token" in r.json()
    new_cookie = re.search(r"refresh_token=([^;]+)", r.headers["set-cookie"]).group(1)
    assert new_cookie != old_cookie
    stale = TestClient(app)
    stale.cookies.set("refresh_token", old_cookie, domain="testserver.local", path="/api/v1/auth")
    assert stale.post("/api/v1/auth/tokens").status_code == 401


def test_role_guard_forbids_buyer():
    from accounts.permissions import require_role

    app = create_app(rate_limit_per_minute=0)

    @app.get("/_admin-probe")
    def probe(_=Depends(require_role("admin"))):
        return "ok"

    client = TestClient(app)
    _, reg = _register(client)
    assert client.get("/_admin-probe", headers=_bearer(reg)).status_code == 403


def _fake_google(monkeypatch, **claims):
    base = {"sub": uuid.uuid4().hex, "email": _email(), "email_verified": True, "name": "Gg User"}
    base.update(claims)
    monkeypatch.setattr(auth_mod, "verify_google_id_token", lambda cred, client_id: base)
    return base


def test_google_creates_user_without_password_then_returns_same_account(client, monkeypatch):
    claims = _fake_google(monkeypatch)
    r1 = client.post("/api/v1/auth/sessions/google", json={"credential": "x"})
    r2 = client.post("/api/v1/auth/sessions/google", json={"credential": "x"})
    assert r1.status_code == r2.status_code == 201
    assert r1.json()["user"]["id"] == r2.json()["user"]["id"]
    with engine.connect() as c:
        pw = c.execute(text("select password_hash from users where email=:e"), {"e": claims["email"]}).scalar_one()
    assert pw is None
    # tài khoản chỉ-Google không đăng nhập được bằng mật khẩu
    assert client.post("/api/v1/auth/sessions", json={"email": claims["email"], "password": PW}).status_code == 401


def test_google_links_existing_password_account(client, monkeypatch):
    email, reg = _register(client)
    _fake_google(monkeypatch, email=email)
    r = client.post("/api/v1/auth/sessions/google", json={"credential": "x"})
    assert r.status_code == 201 and r.json()["user"]["id"] == reg.json()["user"]["id"]


def test_google_unverified_email_rejected(client, monkeypatch):
    _fake_google(monkeypatch, email_verified=False)
    assert client.post("/api/v1/auth/sessions/google", json={"credential": "x"}).status_code == 401


def test_google_outage_is_503_and_creates_nothing(client, monkeypatch):
    def boom(cred, client_id):
        raise auth_mod.GoogleUnavailable("down")
    monkeypatch.setattr(auth_mod, "verify_google_id_token", boom)
    with engine.connect() as c:
        before = c.execute(text("select count(*) from users")).scalar_one()
    r = client.post("/api/v1/auth/sessions/google", json={"credential": "x"})
    assert r.status_code == 503 and "Retry-After" in r.headers
    assert "set-cookie" not in r.headers
    with engine.connect() as c:
        assert c.execute(text("select count(*) from users")).scalar_one() == before


def test_me_reports_login_methods(client, monkeypatch):
    email, reg = _register(client)
    me = client.get("/api/v1/users/me", headers=_bearer(reg)).json()
    assert me["has_password"] is True and me["providers"] == []
    claims = _fake_google(monkeypatch)
    r = client.post("/api/v1/auth/sessions/google", json={"credential": "x"})
    me = client.get("/api/v1/users/me", headers=_bearer(r)).json()
    assert me["has_password"] is False and me["providers"] == ["google"]


def test_signed_in_user_can_link_google_and_then_sign_in_with_it(client, monkeypatch):
    email, reg = _register(client)
    claims = _fake_google(monkeypatch, email=_email())  # email Google khác email tài khoản
    r = client.post("/api/v1/users/me/identities", json={"provider": "google", "credential": "x"}, headers=_bearer(reg))
    assert r.status_code == 201 and r.json()["providers"] == ["google"] and r.json()["email"] == email
    back = client.post("/api/v1/auth/sessions/google", json={"credential": "x"})
    assert back.status_code == 201 and back.json()["user"]["id"] == reg.json()["user"]["id"]
    assert claims["email"] != email


def test_link_google_requires_auth(client):
    r = client.post("/api/v1/users/me/identities", json={"provider": "google", "credential": "x"})
    assert r.status_code == 401


def test_link_google_conflicts(client, monkeypatch):
    _, a = _register(client)
    _, b = _register(client)
    _fake_google(monkeypatch)
    body = {"provider": "google", "credential": "x"}
    assert client.post("/api/v1/users/me/identities", json=body, headers=_bearer(a)).status_code == 201
    again = client.post("/api/v1/users/me/identities", json=body, headers=_bearer(a))
    assert again.status_code == 409 and again.json()["type"] == "/problems/provider-already-linked"
    other = client.post("/api/v1/users/me/identities", json=body, headers=_bearer(b))
    assert other.status_code == 409 and other.json()["type"] == "/problems/google-account-in-use"


def test_link_google_unavailable_changes_nothing(client, monkeypatch):
    _, reg = _register(client)

    def boom(cred, client_id):
        raise auth_mod.GoogleUnavailable("down")

    monkeypatch.setattr(auth_mod, "verify_google_id_token", boom)
    r = client.post("/api/v1/users/me/identities", json={"provider": "google", "credential": "x"}, headers=_bearer(reg))
    assert r.status_code == 503
    assert client.get("/api/v1/users/me", headers=_bearer(reg)).json()["providers"] == []


def test_unlink_google(client, monkeypatch):
    _, reg = _register(client)
    _fake_google(monkeypatch)
    h = _bearer(reg)
    client.post("/api/v1/users/me/identities", json={"provider": "google", "credential": "x"}, headers=h)
    assert client.delete("/api/v1/users/me/identities/google", headers=h).status_code == 204
    assert client.get("/api/v1/users/me", headers=h).json()["providers"] == []
    assert client.delete("/api/v1/users/me/identities/google", headers=h).status_code == 404


def test_cannot_unlink_the_only_login_method(client, monkeypatch):
    _fake_google(monkeypatch)
    r = client.post("/api/v1/auth/sessions/google", json={"credential": "x"})  # tài khoản chỉ-Google
    d = client.delete("/api/v1/users/me/identities/google", headers=_bearer(r))
    assert d.status_code == 409 and d.json()["type"] == "/problems/last-login-method"
    assert client.get("/api/v1/users/me", headers=_bearer(r)).json()["providers"] == ["google"]


def test_unknown_provider_is_404(client):
    _, reg = _register(client)
    assert client.delete("/api/v1/users/me/identities/facebook", headers=_bearer(reg)).status_code == 404


def test_rate_limit_blocks_bursts_on_auth_endpoints():
    limited = TestClient(create_app(rate_limit_per_minute=3))
    codes = [limited.post("/api/v1/auth/sessions", json={"email": _email(), "password": "Sai12345"}).status_code for _ in range(5)]
    assert codes[:3] == [401, 401, 401] and codes[3:] == [429, 429]
    r = limited.post("/api/v1/auth/sessions", json={"email": _email(), "password": "Sai12345"})
    assert r.headers["content-type"].startswith("application/problem+json") and int(r.headers["retry-after"]) > 0
    assert limited.get("/healthz").status_code == 200  # endpoint khác không bị giới hạn


# ---------------------------------------------------------------- Facebook
def _fake_facebook(monkeypatch, **profile):
    base = {"id": uuid.uuid4().hex, "name": "Fb User", "email": _email()}
    base.update(profile)
    monkeypatch.setattr(auth_mod, "verify_facebook_token", lambda token, app_id, secret: base)
    return base


FB = "/api/v1/auth/sessions/facebook"


def test_facebook_creates_user_without_password_then_returns_same_account(client, monkeypatch):
    profile = _fake_facebook(monkeypatch)
    r1 = client.post(FB, json={"access_token": "x"})
    r2 = client.post(FB, json={"access_token": "x"})
    assert r1.status_code == r2.status_code == 201
    assert r1.json()["user"]["id"] == r2.json()["user"]["id"]
    assert r1.json()["user"]["providers"] == ["facebook"] and r1.json()["user"]["has_password"] is False
    assert r1.json()["user"]["email"] == profile["email"]
    assert "refresh_token=" in r1.headers["set-cookie"]


def test_facebook_does_not_auto_merge_into_existing_email_account(client, monkeypatch):
    email, reg = _register(client)
    _fake_facebook(monkeypatch, email=email)
    r = client.post(FB, json={"access_token": "x"})
    assert r.status_code == 409 and r.json()["type"] == "/problems/account-exists"
    assert "set-cookie" not in r.headers
    # sau khi đăng nhập bằng mật khẩu, người dùng tự liên kết được
    linked = client.post("/api/v1/users/me/identities", json={"provider": "facebook", "credential": "x"}, headers=_bearer(reg))
    assert linked.status_code == 201 and linked.json()["providers"] == ["facebook"]
    again = client.post(FB, json={"access_token": "x"})
    assert again.status_code == 201 and again.json()["user"]["id"] == reg.json()["user"]["id"]


def test_facebook_without_email_cannot_create_account(client, monkeypatch):
    _fake_facebook(monkeypatch, email=None)
    r = client.post(FB, json={"access_token": "x"})
    assert r.status_code == 422 and r.json()["type"] == "/problems/facebook-email-missing"


def test_facebook_invalid_token_is_401(client, monkeypatch):
    def bad(token, app_id, secret):
        raise ValueError("bad")
    monkeypatch.setattr(auth_mod, "verify_facebook_token", bad)
    assert client.post(FB, json={"access_token": "x"}).status_code == 401


def test_facebook_outage_is_503_and_creates_nothing(client, monkeypatch):
    def boom(token, app_id, secret):
        raise auth_mod.FacebookUnavailable("down")
    monkeypatch.setattr(auth_mod, "verify_facebook_token", boom)
    with engine.connect() as c:
        before = c.execute(text("select count(*) from users")).scalar_one()
    r = client.post(FB, json={"access_token": "x"})
    assert r.status_code == 503 and "retry-after" in r.headers and "set-cookie" not in r.headers
    with engine.connect() as c:
        assert c.execute(text("select count(*) from users")).scalar_one() == before


def test_facebook_not_configured_is_503(monkeypatch):
    c = TestClient(create_app(rate_limit_per_minute=0))  # không đặt FACEBOOK_APP_ID/SECRET
    monkeypatch.delenv("FACEBOOK_APP_ID", raising=False)
    r = c.post(FB, json={"access_token": "x"})
    assert r.status_code == 503 and r.json()["type"] == "/problems/facebook-unavailable"


def test_facebook_account_in_use_by_someone_else(client, monkeypatch):
    _, a = _register(client)
    _, b = _register(client)
    _fake_facebook(monkeypatch)
    body = {"provider": "facebook", "credential": "x"}
    assert client.post("/api/v1/users/me/identities", json=body, headers=_bearer(a)).status_code == 201
    other = client.post("/api/v1/users/me/identities", json=body, headers=_bearer(b))
    assert other.status_code == 409 and other.json()["type"] == "/problems/facebook-account-in-use"


def test_can_unlink_one_provider_when_another_remains_even_without_password(client, monkeypatch):
    _fake_google(monkeypatch)
    r = client.post("/api/v1/auth/sessions/google", json={"credential": "x"})  # tài khoản chỉ-Google
    h = _bearer(r)
    _fake_facebook(monkeypatch)
    assert client.post("/api/v1/users/me/identities", json={"provider": "facebook", "credential": "x"}, headers=h).status_code == 201
    assert client.get("/api/v1/users/me", headers=h).json()["providers"] == ["facebook", "google"]
    assert client.delete("/api/v1/users/me/identities/facebook", headers=h).status_code == 204
    last = client.delete("/api/v1/users/me/identities/google", headers=h)
    assert last.status_code == 409 and last.json()["type"] == "/problems/last-login-method"


def test_verify_facebook_token_checks_app_id_and_handles_outage(monkeypatch):
    """Hàm xác minh thật (không mock) với Graph API giả: sai app -> ValueError, 5xx/mạng -> Unavailable."""
    import requests

    class Resp:
        def __init__(self, status, body):
            self.status_code, self._body = status, body
        def json(self):
            return self._body

    def make(dbg, me=None, raise_exc=None):
        def fake_get(url, **kw):
            if raise_exc:
                raise raise_exc
            return dbg if url.endswith("/debug_token") else me
        return fake_get

    good = Resp(200, {"data": {"is_valid": True, "app_id": "APP", "user_id": "1"}})
    me = Resp(200, {"id": "1", "name": "A", "email": "a@x.com"})
    monkeypatch.setattr(requests, "get", make(good, me))
    assert auth_mod.verify_facebook_token("t", "APP", "SECRET")["id"] == "1"

    monkeypatch.setattr(requests, "get", make(Resp(200, {"data": {"is_valid": True, "app_id": "OTHER", "user_id": "1"}}), me))
    with pytest.raises(ValueError):
        auth_mod.verify_facebook_token("t", "APP", "SECRET")  # token của app khác

    monkeypatch.setattr(requests, "get", make(Resp(200, {"data": {"is_valid": False}}), me))
    with pytest.raises(ValueError):
        auth_mod.verify_facebook_token("t", "APP", "SECRET")

    monkeypatch.setattr(requests, "get", make(Resp(503, {})))
    with pytest.raises(auth_mod.FacebookUnavailable):
        auth_mod.verify_facebook_token("t", "APP", "SECRET")

    monkeypatch.setattr(requests, "get", make(None, raise_exc=requests.ConnectionError("net")))
    with pytest.raises(auth_mod.FacebookUnavailable):
        auth_mod.verify_facebook_token("t", "APP", "SECRET")

    with pytest.raises(auth_mod.FacebookUnavailable):
        auth_mod.verify_facebook_token("t", "", "")  # chưa cấu hình

