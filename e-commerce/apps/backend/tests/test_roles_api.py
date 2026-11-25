"""Luồng auth đủ 3 vai trò: buyer, seller, admin (phân quyền, khóa tài khoản, đổi mật khẩu)."""
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from accounts import authentication
from app import create_app
from db import engine, new_id

PW = "Matkhau123"
DOM = "@rolestest.local"


@pytest.fixture(scope="module")
def client():
    return TestClient(create_app(rate_limit_per_minute=0, email_backend="memory"))


@pytest.fixture(scope="module", autouse=True)
def _cleanup():
    yield
    with engine.begin() as c:
        c.execute(text(f"delete from seller_applications where user_id in (select id from users where email like '%{DOM}')"))
        c.execute(text(f"delete from shops where owner_user_id in (select id from users where email like '%{DOM}')"))
        c.execute(text(f"delete from users where email like '%{DOM}'"))


def _signup(client, name="Nguoi Dung"):
    email = f"u{uuid.uuid4().hex[:10]}{DOM}"
    r = client.post("/api/v1/users", json={"email": email, "password": PW, "full_name": name})
    assert r.status_code == 201
    return email, r.json()["user"]["id"], {"Authorization": f"Bearer {r.json()['access_token']}"}


def _admin(client):
    email, uid, _ = _signup(client, "Admin")
    with engine.begin() as c:
        c.execute(text("update users set role='admin' where id=:i"), {"i": uid})
    r = client.post("/api/v1/auth/sessions", json={"email": email, "password": PW})
    return uid, {"Authorization": f"Bearer {r.json()['access_token']}"}


def _seller(client):
    email, uid, h = _signup(client, "Seller")
    with engine.begin() as c:
        c.execute(text("update users set email_verified_at = now() where id=:i"), {"i": uid})
    code = client.get("/api/v1/provinces").json()[0]["code"]
    app_id = client.post("/api/v1/seller-applications", headers=h, json={"name": "Shop role", "province_code": code}).json()["id"]
    _, adm = _admin(client)
    assert client.post(f"/api/v1/admin/seller-applications/{app_id}/approval", headers=adm).status_code == 200
    return email, uid, h


def test_admin_endpoints_forbidden_for_buyer_and_seller(client):
    _, _, buyer = _signup(client)
    _, _, seller = _seller(client)
    for h in (buyer, seller):
        assert client.get("/api/v1/admin/users", headers=h).status_code == 403
    assert client.get("/api/v1/admin/users").status_code == 401


def test_admin_lists_filters_and_paginates(client):
    _, adm = _admin(client)
    for _ in range(3):
        _signup(client, "Loc Theo Ten")
    r = client.get("/api/v1/admin/users", headers=adm, params={"q": "loc theo ten", "limit": 2})
    assert r.status_code == 200
    body = r.json()
    assert len(body["items"]) == 2 and body["next_cursor"]
    r2 = client.get("/api/v1/admin/users", headers=adm, params={"q": "loc theo ten", "limit": 2, "cursor": body["next_cursor"]})
    ids = {u["id"] for u in body["items"]} | {u["id"] for u in r2.json()["items"]}
    assert len(ids) >= 3
    assert client.get("/api/v1/admin/users", headers=adm, params={"cursor": "###"}).status_code == 400
    only_admin = client.get("/api/v1/admin/users", headers=adm, params={"role": "admin", "q": DOM}).json()["items"]
    assert only_admin and all(u["role"] == "admin" for u in only_admin)


def test_suspend_revokes_sessions_and_blocks_login_until_restored(client):
    _, adm = _admin(client)
    email, uid, h = _signup(client)
    r = client.patch(f"/api/v1/admin/users/{uid}", headers=adm, json={"status": "suspended"})
    assert r.status_code == 200 and r.json()["status"] == "suspended"
    assert client.get("/api/v1/users/me", headers=h).status_code == 401  # phiên đã bị thu hồi
    login = client.post("/api/v1/auth/sessions", json={"email": email, "password": PW})
    assert login.status_code == 403 and login.json()["type"] == "/problems/account-suspended"
    assert client.patch(f"/api/v1/admin/users/{uid}", headers=adm, json={"status": "active"}).status_code == 200
    assert client.post("/api/v1/auth/sessions", json={"email": email, "password": PW}).status_code == 201


def test_wrong_password_still_401_for_suspended_account(client):
    _, adm = _admin(client)
    email, uid, _ = _signup(client)
    client.patch(f"/api/v1/admin/users/{uid}", headers=adm, json={"status": "suspended"})
    r = client.post("/api/v1/auth/sessions", json={"email": email, "password": "SaiMatKhau1"})
    assert r.status_code == 401  # không lộ trạng thái cho người không có mật khẩu


def test_refresh_rejected_when_suspended(client):
    _, adm = _admin(client)
    c2 = TestClient(client.app)
    email, uid, _ = _signup(c2)  # c2 giữ cookie refresh
    client.patch(f"/api/v1/admin/users/{uid}", headers=adm, json={"status": "suspended"})
    assert c2.post("/api/v1/auth/tokens").status_code == 401


def test_admin_cannot_modify_self_and_seller_role_is_protected(client):
    uid, adm = _admin(client)
    r = client.patch(f"/api/v1/admin/users/{uid}", headers=adm, json={"status": "suspended"})
    assert r.status_code == 409 and r.json()["type"] == "/problems/cannot-modify-self"
    _, sid, _ = _seller(client)
    r = client.patch(f"/api/v1/admin/users/{sid}", headers=adm, json={"role": "buyer"})
    assert r.status_code == 409 and r.json()["type"] == "/problems/seller-has-shop"
    assert client.patch(f"/api/v1/admin/users/{sid}", headers=adm, json={"role": "seller"}).status_code == 422
    assert client.get(f"/api/v1/admin/users/{sid}", headers=adm).json()["has_shop"] is True
    assert client.get(f"/api/v1/admin/users/{uuid.uuid4()}", headers=adm).status_code == 404


def test_admin_promotes_and_demotes_buyer(client):
    _, adm = _admin(client)
    _, uid, h = _signup(client)
    assert client.patch(f"/api/v1/admin/users/{uid}", headers=adm, json={"role": "admin"}).json()["role"] == "admin"
    assert client.get("/api/v1/admin/users", headers=h).status_code == 200  # token cũ dùng được quyền mới ngay
    assert client.patch(f"/api/v1/admin/users/{uid}", headers=adm, json={"role": "buyer"}).json()["role"] == "buyer"
    assert client.get("/api/v1/admin/users", headers=h).status_code == 403


def test_admin_cannot_open_shop(client):
    _, adm = _admin(client)
    code = client.get("/api/v1/provinces").json()[0]["code"]
    assert client.post("/api/v1/seller-applications", headers=adm, json={"name": "Shop admin", "province_code": code}).status_code == 403


def test_change_password_rules_and_revokes_other_sessions(client):
    c_other = TestClient(client.app)
    email, _, h = _signup(client)
    other = c_other.post("/api/v1/auth/sessions", json={"email": email, "password": PW}).json()
    oh = {"Authorization": f"Bearer {other['access_token']}"}
    url = "/api/v1/users/me/password"
    assert client.put(url, headers=h, json={"current_password": "SaiMatKhau1", "new_password": "MatkhauMoi1"}).status_code == 422
    assert client.put(url, headers=h, json={"current_password": PW, "new_password": PW}).status_code == 422
    assert client.put(url, headers=h, json={"current_password": PW, "new_password": "yeu"}).status_code == 422
    assert client.put(url, headers=h, json={"current_password": PW, "new_password": "MatkhauMoi1"}).status_code == 204
    assert client.get("/api/v1/users/me", headers=h).status_code == 200  # phiên hiện tại giữ nguyên
    assert client.get("/api/v1/users/me", headers=oh).status_code == 401  # phiên khác bị đăng xuất
    assert client.post("/api/v1/auth/sessions", json={"email": email, "password": PW}).status_code == 401
    assert client.post("/api/v1/auth/sessions", json={"email": email, "password": "MatkhauMoi1"}).status_code == 201


def test_social_only_account_can_set_first_password(client):
    email, uid, h = _signup(client)
    with engine.begin() as c:
        c.execute(text("update users set password_hash=null where id=:i"), {"i": uid})
    assert client.put("/api/v1/users/me/password", headers=h, json={"new_password": "MatkhauMoi1"}).status_code == 204
    assert client.post("/api/v1/auth/sessions", json={"email": email, "password": "MatkhauMoi1"}).status_code == 201


def test_create_admin_script_is_idempotent(client, monkeypatch):
    import importlib.util
    import pathlib

    spec = importlib.util.spec_from_file_location(
        "create_admin", pathlib.Path(__file__).resolve().parent.parent / "scripts" / "create_admin.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    email = f"adm{uuid.uuid4().hex[:8]}{DOM}"
    monkeypatch.setenv("ADMIN_EMAIL", email)
    monkeypatch.setenv("ADMIN_PASSWORD", "Admin12345")
    mod.main()
    mod.main()
    r = client.post("/api/v1/auth/sessions", json={"email": email, "password": "Admin12345"})
    assert r.status_code == 201 and r.json()["user"]["role"] == "admin"
