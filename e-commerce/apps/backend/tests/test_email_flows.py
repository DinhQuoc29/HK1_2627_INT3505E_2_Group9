"""Xác minh email và quên mật khẩu qua email (backend email = memory)."""
import re
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app import create_app
from db import engine

PW = "Matkhau123"
DOM = "@emailtest.local"


@pytest.fixture(scope="module")
def client():
    return TestClient(create_app(rate_limit_per_minute=0, email_backend="memory", email_resend_cooldown_seconds=60))


@pytest.fixture(scope="module", autouse=True)
def _cleanup():
    yield
    with engine.begin() as c:
        c.execute(text(f"delete from users where email like '%{DOM}'"))


def _signup(client):
    email = f"u{uuid.uuid4().hex[:10]}{DOM}"
    r = client.post("/api/v1/users", json={"email": email, "password": PW, "full_name": "Nguoi Dung"})
    assert r.status_code == 201
    return email, r.json()["user"], {"Authorization": f"Bearer {r.json()['access_token']}"}


def _last_token(client, to, path):
    mails = [m for m in client.app.state.mailer.outbox if m.to == to and path in m.text]
    assert mails, f"không có email {path} cho {to}"
    return re.search(rf"{path}\?token=([\w-]+)", mails[-1].text).group(1)


def test_register_sends_verification_email_and_confirm_verifies(client):
    email, user, h = _signup(client)
    assert user["email_verified"] is False
    token = _last_token(client, email, "/verify-email")
    r = client.post("/api/v1/auth/email-verifications/confirmation", json={"token": token})
    assert r.status_code == 204
    assert client.get("/api/v1/users/me", headers=h).json()["email_verified"] is True


def test_verification_token_is_single_use_and_garbage_rejected(client):
    email, _, _ = _signup(client)
    token = _last_token(client, email, "/verify-email")
    assert client.post("/api/v1/auth/email-verifications/confirmation", json={"token": token}).status_code == 204
    r = client.post("/api/v1/auth/email-verifications/confirmation", json={"token": token})
    assert r.status_code == 400 and r.json()["type"] == "/problems/invalid-email-token"
    assert client.post("/api/v1/auth/email-verifications/confirmation", json={"token": "x" * 40}).status_code == 400
    assert client.post("/api/v1/auth/email-verifications/confirmation", json={"token": "ngan"}).status_code == 422


def test_expired_token_rejected(client):
    email, user, _ = _signup(client)
    token = _last_token(client, email, "/verify-email")
    with engine.begin() as c:
        c.execute(text("update email_tokens set expires_at = now() - interval '1 minute' where user_id = :u"), {"u": user["id"]})
    assert client.post("/api/v1/auth/email-verifications/confirmation", json={"token": token}).status_code == 400


def test_resend_has_cooldown_and_invalidates_old_link(client):
    email, user, h = _signup(client)
    old = _last_token(client, email, "/verify-email")
    r = client.post("/api/v1/auth/email-verifications", headers=h)
    assert r.status_code == 429 and int(r.headers["retry-after"]) > 0
    with engine.begin() as c:  # giả lập đã qua thời gian chờ
        c.execute(text("update email_tokens set created_at = now() - interval '5 minutes' where user_id = :u"), {"u": user["id"]})
    assert client.post("/api/v1/auth/email-verifications", headers=h).status_code == 202
    new = _last_token(client, email, "/verify-email")
    assert new != old
    assert client.post("/api/v1/auth/email-verifications/confirmation", json={"token": old}).status_code == 400
    assert client.post("/api/v1/auth/email-verifications/confirmation", json={"token": new}).status_code == 204
    assert client.post("/api/v1/auth/email-verifications", headers=h).status_code == 409  # đã xác minh


def test_resend_requires_login(client):
    assert client.post("/api/v1/auth/email-verifications").status_code == 401


def test_forgot_password_does_not_reveal_whether_email_exists(client):
    known, _, _ = _signup(client)
    a = client.post("/api/v1/auth/password-resets", json={"email": known})
    b = client.post("/api/v1/auth/password-resets", json={"email": f"khongco{uuid.uuid4().hex[:6]}{DOM}"})
    assert a.status_code == b.status_code == 202 and a.json() == b.json()
    assert any(m.to == known and "/reset-password" in m.text for m in client.app.state.mailer.outbox)
    assert not any("khongco" in m.to for m in client.app.state.mailer.outbox)
    assert client.post("/api/v1/auth/password-resets", json={"email": "khong-hop-le"}).status_code == 422


def test_reset_password_flow_revokes_sessions_and_verifies_email(client):
    email, _, h = _signup(client)
    client.post("/api/v1/auth/password-resets", json={"email": email})
    token = _last_token(client, email, "/reset-password")
    assert client.post("/api/v1/auth/password-resets/confirmation", json={"token": token, "new_password": "yeu"}).status_code == 422
    r = client.post("/api/v1/auth/password-resets/confirmation", json={"token": token, "new_password": "MatkhauMoi9"})
    assert r.status_code == 204
    assert client.get("/api/v1/users/me", headers=h).status_code == 401  # phiên cũ bị thu hồi
    assert client.post("/api/v1/auth/sessions", json={"email": email, "password": PW}).status_code == 401
    login = client.post("/api/v1/auth/sessions", json={"email": email, "password": "MatkhauMoi9"})
    assert login.status_code == 201 and login.json()["user"]["email_verified"] is True
    again = client.post("/api/v1/auth/password-resets/confirmation", json={"token": token, "new_password": "MatkhauMoi8"})
    assert again.status_code == 400 and again.json()["type"] == "/problems/invalid-reset-token"


def test_reset_request_cooldown_and_newer_link_replaces_older(client):
    email, user, _ = _signup(client)
    client.post("/api/v1/auth/password-resets", json={"email": email})
    client.post("/api/v1/auth/password-resets", json={"email": email})  # trong thời gian chờ: bỏ qua im lặng
    assert sum(1 for m in client.app.state.mailer.outbox if m.to == email and "/reset-password" in m.text) == 1
    first = _last_token(client, email, "/reset-password")
    with engine.begin() as c:
        c.execute(text("update email_tokens set created_at = now() - interval '5 minutes' where user_id = :u"), {"u": user["id"]})
    client.post("/api/v1/auth/password-resets", json={"email": email})
    second = _last_token(client, email, "/reset-password")
    assert first != second
    assert client.post("/api/v1/auth/password-resets/confirmation", json={"token": first, "new_password": "MatkhauMoi9"}).status_code == 400
    assert client.post("/api/v1/auth/password-resets/confirmation", json={"token": second, "new_password": "MatkhauMoi9"}).status_code == 204


def test_suspended_account_gets_no_reset_email(client):
    email, user, _ = _signup(client)
    with engine.begin() as c:
        c.execute(text("update users set status='suspended' where id=:i"), {"i": user["id"]})
    before = len(client.app.state.mailer.outbox)
    assert client.post("/api/v1/auth/password-resets", json={"email": email}).status_code == 202
    assert len(client.app.state.mailer.outbox) == before


def test_social_only_account_can_set_password_via_reset(client):
    email, user, _ = _signup(client)
    with engine.begin() as c:
        c.execute(text("update users set password_hash=null where id=:i"), {"i": user["id"]})
    client.post("/api/v1/auth/password-resets", json={"email": email})
    token = _last_token(client, email, "/reset-password")
    assert client.post("/api/v1/auth/password-resets/confirmation", json={"token": token, "new_password": "MatkhauMoi9"}).status_code == 204
    assert client.post("/api/v1/auth/sessions", json={"email": email, "password": "MatkhauMoi9"}).status_code == 201
