"""Xác minh ID token Google bằng code THẬT (google-auth), chỉ giả lập khâu tải chứng chỉ công khai của Google.

Token được ký cục bộ bằng khóa RSA của test, nên kiểm tra được chữ ký, audience, issuer, hạn dùng mà không cần mạng.
"""
import time
import uuid

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from google.auth import exceptions as g_exc
from google.oauth2 import id_token as g_id_token
from sqlalchemy import text

import accounts.authentication as auth_mod
from app import create_app
from db import engine

CLIENT_ID = "123-test.apps.googleusercontent.com"
KID = "test-key-1"


def _keypair():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
    public = key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
    return private, public.decode()


PRIVATE, PUBLIC = _keypair()
OTHER_PRIVATE, _ = _keypair()


def _token(key=PRIVATE, **over):
    now = int(time.time())
    claims = {
        "iss": "https://accounts.google.com", "aud": CLIENT_ID, "sub": uuid.uuid4().hex,
        "email": f"g{uuid.uuid4().hex[:8]}@authtest.local", "email_verified": True, "name": "Gg Real",
        "iat": now, "exp": now + 600,
    }
    claims.update(over)
    return jwt.encode(claims, key, algorithm="RS256", headers={"kid": KID})


@pytest.fixture(autouse=True)
def _google_certs(monkeypatch):
    monkeypatch.setattr(g_id_token, "_fetch_certs", lambda request, url: {KID: PUBLIC})


@pytest.fixture(scope="module", autouse=True)
def _cleanup():
    yield
    with engine.begin() as c:
        c.execute(text("delete from users where email like '%@authtest.local'"))


@pytest.fixture
def client():
    return TestClient(create_app(google_client_id=CLIENT_ID, rate_limit_per_minute=0))


# ---- hàm xác minh
def test_valid_token_is_accepted():
    claims = auth_mod.verify_google_id_token(_token(), CLIENT_ID)
    assert claims["email_verified"] is True and claims["aud"] == CLIENT_ID


@pytest.mark.parametrize("name,token", [
    ("sai audience (token của app khác)", lambda: _token(aud="other.apps.googleusercontent.com")),
    ("hết hạn", lambda: _token(iat=int(time.time()) - 7200, exp=int(time.time()) - 3600)),
    ("sai issuer", lambda: _token(iss="https://evil.example.com")),
    ("chữ ký giả (khóa khác)", lambda: _token(key=OTHER_PRIVATE)),
    ("không phải JWT", lambda: "khong-phai-jwt"),
])
def test_invalid_tokens_raise_value_error(name, token):
    with pytest.raises(ValueError):
        auth_mod.verify_google_id_token(token(), CLIENT_ID)


def test_fetching_certs_failure_is_reported_as_unavailable(monkeypatch):
    def boom(request, url):
        raise g_exc.TransportError("mạng lỗi")
    monkeypatch.setattr(g_id_token, "_fetch_certs", boom)
    with pytest.raises(auth_mod.GoogleUnavailable):
        auth_mod.verify_google_id_token(_token(), CLIENT_ID)


# ---- qua API (không mock hàm xác minh)
def test_api_login_with_real_verification_creates_then_reuses_account(client):
    token = _token()
    r1 = client.post("/api/v1/auth/sessions/google", json={"credential": token})
    r2 = client.post("/api/v1/auth/sessions/google", json={"credential": token})
    assert r1.status_code == r2.status_code == 201
    assert r1.json()["user"]["id"] == r2.json()["user"]["id"]
    assert r1.json()["user"]["providers"] == ["google"]


@pytest.mark.parametrize("token", [
    lambda: _token(aud="other.apps.googleusercontent.com"),
    lambda: _token(iat=int(time.time()) - 7200, exp=int(time.time()) - 3600),
    lambda: _token(iss="https://evil.example.com"),
    lambda: _token(key=OTHER_PRIVATE),
    lambda: _token(email_verified=False),
])
def test_api_rejects_bad_tokens_with_401_never_500(client, token):
    r = client.post("/api/v1/auth/sessions/google", json={"credential": token()})
    assert r.status_code == 401
    assert "set-cookie" not in r.headers


def test_api_without_client_id_reports_unavailable_not_crash():
    c = TestClient(create_app(google_client_id="", rate_limit_per_minute=0))
    r = c.post("/api/v1/auth/sessions/google", json={"credential": _token()})
    assert r.status_code == 503 and r.json()["type"] == "/problems/google-unavailable"
