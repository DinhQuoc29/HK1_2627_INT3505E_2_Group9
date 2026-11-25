"""Đăng ký người bán qua hồ sơ + admin duyệt: buyer (đã xác minh email) -> pending -> approved -> seller + shop."""
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app import create_app
from db import engine

PW = "Matkhau123"
DOM = "@shoptest.local"


@pytest.fixture(scope="module")
def client():
    return TestClient(create_app(rate_limit_per_minute=0, email_backend="memory"))


@pytest.fixture(scope="module", autouse=True)
def _cleanup():
    yield
    with engine.begin() as c:
        c.execute(text(
            "delete from products where shop_id in (select s.id from shops s join users u on u.id=s.owner_user_id where u.email like :email)"
        ), {"email": f"%{DOM}"})
        c.execute(text(f"delete from seller_applications where user_id in (select id from users where email like '%{DOM}')"))
        c.execute(text(f"delete from shops where owner_user_id in (select id from users where email like '%{DOM}')"))
        c.execute(text(f"delete from users where email like '%{DOM}'"))


def _signup(client, verified=True, name="Nguoi Ban"):
    email = f"u{uuid.uuid4().hex[:10]}{DOM}"
    r = client.post("/api/v1/users", json={"email": email, "password": PW, "full_name": name})
    assert r.status_code == 201
    uid = r.json()["user"]["id"]
    if verified:
        with engine.begin() as c:
            c.execute(text("update users set email_verified_at = now() where id = :i"), {"i": uid})
    return email, uid, {"Authorization": f"Bearer {r.json()['access_token']}"}


def _admin(client):
    email, uid, _ = _signup(client, name="Admin")
    with engine.begin() as c:
        c.execute(text("update users set role='admin' where id=:i"), {"i": uid})
    r = client.post("/api/v1/auth/sessions", json={"email": email, "password": PW})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _code(client):
    return client.get("/api/v1/provinces").json()[0]["code"]


def _apply(client, h, name="  Cửa hàng   Của An "):
    return client.post("/api/v1/seller-applications", headers=h, json={"name": name, "province_code": _code(client)})


def test_provinces_public(client):
    r = client.get("/api/v1/provinces")
    assert r.status_code == 200 and len(r.json()) == 34


def test_apply_requires_auth_and_verified_email(client):
    assert client.post("/api/v1/seller-applications", json={"name": "Shop", "province_code": "HN"}).status_code == 401
    _, _, h = _signup(client, verified=False)
    r = _apply(client, h)
    assert r.status_code == 403 and r.json()["type"] == "/problems/email-not-verified"


def test_apply_creates_pending_and_does_not_promote(client):
    _, _, h = _signup(client)
    r = _apply(client, h)
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "pending" and body["shop_name"] == "Cửa hàng Của An" and body["province_name"]
    assert client.get("/api/v1/users/me", headers=h).json()["role"] == "buyer"
    assert client.get("/api/v1/shops/me", headers=h).status_code == 403
    assert client.get("/api/v1/seller-applications/me", headers=h).json()["id"] == body["id"]


def test_second_pending_application_conflicts(client):
    email, _, h = _signup(client)
    assert _apply(client, h).status_code == 201
    r = _apply(client, h)
    assert r.status_code == 409 and r.json()["type"] == "/problems/application-pending"
    receipts = [
        mail for mail in client.app.state.mailer.outbox
        if mail.to == email and mail.subject == "Đã nhận hồ sơ đăng ký bán hàng"
    ]
    assert len(receipts) == 1
    assert "Cửa hàng Của An" in receipts[0].text
    assert "/seller/register" in receipts[0].text


def test_validation_and_unknown_province(client):
    _, _, h = _signup(client)
    assert client.post("/api/v1/seller-applications", headers=h, json={"name": "ab", "province_code": "HN"}).status_code == 422
    r = client.post("/api/v1/seller-applications", headers=h, json={"name": "Shop hợp lệ", "province_code": "ZZ"})
    assert r.status_code == 422 and r.json()["errors"][0]["field"] == "province_code"
    assert client.get("/api/v1/seller-applications/me", headers=h).status_code == 404


def test_only_admin_reviews(client):
    _, _, buyer = _signup(client)
    app_id = _apply(client, buyer).json()["id"]
    assert client.get("/api/v1/admin/seller-applications", headers=buyer).status_code == 403
    assert client.post(f"/api/v1/admin/seller-applications/{app_id}/approval", headers=buyer).status_code == 403
    assert client.get("/api/v1/admin/seller-applications").status_code == 401


def test_admin_approves_and_user_becomes_seller_with_same_token(client):
    adm = _admin(client)
    email, uid, h = _signup(client)
    app_id = _apply(client, h).json()["id"]
    listed = client.get("/api/v1/admin/seller-applications", headers=adm, params={"status": "pending"}).json()["items"]
    assert any(i["id"] == app_id and i["applicant_email"] == email for i in listed)
    r = client.post(f"/api/v1/admin/seller-applications/{app_id}/approval", headers=adm)
    assert r.status_code == 200 and r.json()["status"] == "approved"
    assert client.get("/api/v1/users/me", headers=h).json()["role"] == "seller"
    shop = client.get("/api/v1/shops/me", headers=h).json()
    assert shop["name"] == "Cửa hàng Của An"
    again = client.post(f"/api/v1/admin/seller-applications/{app_id}/approval", headers=adm)
    assert again.status_code == 409 and again.json()["type"] == "/problems/application-not-pending"
    assert _apply(client, h).status_code == 409  # đã là seller


def test_admin_rejects_with_reason_and_user_can_reapply(client):
    adm = _admin(client)
    email, _, h = _signup(client)
    app_id = _apply(client, h).json()["id"]
    assert client.post(f"/api/v1/admin/seller-applications/{app_id}/rejection", headers=adm, json={"reason": "x"}).status_code == 422
    r = client.post(f"/api/v1/admin/seller-applications/{app_id}/rejection", headers=adm, json={"reason": "Tên shop vi phạm"})
    assert r.status_code == 200 and r.json()["status"] == "rejected"
    mine = client.get("/api/v1/seller-applications/me", headers=h).json()
    assert mine["status"] == "rejected" and mine["reject_reason"] == "Tên shop vi phạm"
    rejected = next(
        mail for mail in client.app.state.mailer.outbox
        if mail.to == email and mail.subject == "Hồ sơ người bán chưa được duyệt"
    )
    assert "Tên shop vi phạm" in rejected.text and "/seller/register" in rejected.text
    assert client.get("/api/v1/users/me", headers=h).json()["role"] == "buyer"
    assert _apply(client, h, "Shop nộp lại").status_code == 201
    assert client.get("/api/v1/seller-applications/me", headers=h).json()["status"] == "pending"


def test_unknown_application_and_bad_cursor(client):
    adm = _admin(client)
    assert client.post(f"/api/v1/admin/seller-applications/{uuid.uuid4()}/approval", headers=adm).status_code == 404
    assert client.get("/api/v1/admin/seller-applications", headers=adm, params={"cursor": "###"}).status_code == 400


def test_admin_cannot_apply(client):
    assert _apply(client, _admin(client)).status_code == 403


def test_decision_emails_are_sent(client):
    adm = _admin(client)
    mailer = client.app.state.mailer
    email, _, h = _signup(client)
    app_id = _apply(client, h).json()["id"]
    client.post(f"/api/v1/admin/seller-applications/{app_id}/approval", headers=adm)
    assert any(m.to == email and "được duyệt" in m.subject for m in mailer.outbox)


def test_seller_products_save_images_stock_and_respect_shop_ownership(client):
    admin = _admin(client)
    sellers = []
    for i in range(2):
        _, _, headers = _signup(client)
        pending = _apply(client, headers, name=f"Shop test {i + 1}").json()["id"]
        assert client.post(f"/api/v1/admin/seller-applications/{pending}/approval", headers=admin).status_code == 200
        sellers.append(headers)
    owner, other = sellers
    parent_id, category_id = uuid.uuid4(), uuid.uuid4()
    with engine.begin() as connection:
        connection.execute(text("insert into categories (id,name,slug,level) values (:id,:name,:slug,1)"),
                           {"id": parent_id, "name": f"Test {parent_id}", "slug": str(parent_id)})
        connection.execute(text("insert into categories (id,parent_id,name,slug,level) values (:id,:parent,'Danh mục test',:slug,2)"),
                           {"id": category_id, "parent": parent_id, "slug": str(category_id)})
    base = "/api/v1/shops/me"
    first = "https://example.com/cover.jpg"
    second = "https://example.com/side.jpg"
    payload = {
        "name": "Đồng Hồ Điện Tử", "description": "Sản phẩm kiểm thử", "category_id": str(category_id),
        "price": 125000, "quantity": 7, "images": [first, second],
    }
    try:
        categories = client.get(f"{base}/product-categories", headers=owner).json()
        assert any(c["id"] == str(category_id) for c in categories)
        assert all(c["id"] != str(parent_id) for c in categories)
        assert client.post(f"{base}/products", headers=owner, json={**payload, "category_id": str(parent_id)}).status_code == 422
        assert client.post(f"{base}/products", headers=owner, json={**payload, "quantity": -1}).status_code == 422

        created = client.post(f"{base}/products", headers=owner, json=payload)
        assert created.status_code == 201
        product = created.json()
        path = f"{base}/products/{product['id']}"
        assert product["quantity"] == 7 and product["images"] == [first, second]
        assert client.get(f"{base}/products", headers=other).json()["items"] == []
        assert client.put(path, headers=other, json=payload).status_code == 404
        assert client.patch(f"{path}/status", headers=other, json={"status": "inactive"}).status_code == 404

        updated = client.put(path, headers=owner, json={**payload, "quantity": 0, "price": 100000, "images": [second]})
        assert updated.status_code == 200
        assert updated.json()["images"] == [second] and updated.json()["quantity"] == 0
        hidden = client.patch(f"{path}/status", headers=owner, json={"status": "inactive"})
        assert hidden.status_code == 200 and hidden.json()["status"] == "inactive"
        params = {"q": "dong ho", "status": "inactive"}
        rows = client.get(f"{base}/products", headers=owner, params=params).json()["items"]
        assert len(rows) == 1 and rows[0]["id"] == product["id"]
        assert rows[0]["images"] == [second] and rows[0]["price"] == 100000 and rows[0]["quantity"] == 0
        assert client.patch(f"{path}/status", headers=owner, json={"status": "active"}).json()["status"] == "active"
    finally:
        with engine.begin() as connection:
            connection.execute(text("delete from products where category_id=:category"), {"category": category_id})
            connection.execute(text("delete from categories where id=:id"), {"id": category_id})
            connection.execute(text("delete from categories where id=:id"), {"id": parent_id})
