"""Đăng ký người bán qua hồ sơ + admin duyệt: buyer (đã xác minh email) -> pending -> approved -> seller + shop."""
import uuid
from concurrent.futures import ThreadPoolExecutor

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


def test_only_shop_owner_can_save_profile_and_see_its_empty_statistics(client):
    admin = _admin(client)
    _, _, seller = _signup(client)
    provinces = client.get("/api/v1/provinces").json()
    target = provinces[1]
    path = "/api/v1/shops/me"
    body = {"name": "  Shop   đã đổi tên  ", "province_code": target["code"]}
    assert client.put(path, headers=seller, json=body).status_code == 403
    assert client.get(f"{path}/statistics", headers=seller).status_code == 403
    assert client.get(f"{path}/statistics", headers=admin).status_code == 403

    application_id = _apply(client, seller).json()["id"]
    assert client.post(f"/api/v1/admin/seller-applications/{application_id}/approval", headers=admin).status_code == 200
    original = client.get(path, headers=seller).json()
    invalid = client.put(path, headers=seller, json={**body, "province_code": "ZZ"})
    assert invalid.status_code == 422 and invalid.json()["errors"][0]["field"] == "province_code"
    assert client.get(path, headers=seller).json() == original

    saved = client.put(path, headers=seller, json=body)
    assert saved.status_code == 200 and saved.headers["cache-control"] == "no-store"
    assert saved.json() == {**original, "name": "Shop đã đổi tên", "province": target}
    assert client.get(path, headers=seller).json() == saved.json()

    stats = client.get(f"{path}/statistics", headers=seller)
    assert stats.status_code == 200 and stats.headers["cache-control"] == "no-store"
    assert stats.json() == {
        "total_orders": 0, "captured_orders": 0, "recorded_revenue_vnd": "0",
        "orders_by_status": {"pending_payment": 0, "paid": 0, "shipping": 0, "completed": 0, "cancelled": 0},
    }


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


def test_order_fulfillment_is_scoped_to_the_shop_and_serialized(client):
    admin = _admin(client)
    _, buyer_id, buyer = _signup(client)
    sellers = []
    for index in range(2):
        _, _, headers = _signup(client)
        application = _apply(client, headers, name=f"Gian hàng giao đơn {index}").json()["id"]
        approved = client.post(f"/api/v1/admin/seller-applications/{application}/approval", headers=admin)
        assert approved.status_code == 200
        sellers.append((headers, client.get("/api/v1/shops/me", headers=headers).json()["id"]))
    (owner, shop_id), (other, other_shop_id) = sellers
    checkout_id, another_checkout_id, order_id, second_id, sibling_id, category_id, product_id = [uuid.uuid4() for _ in range(7)]
    payment_id, refunded_payment_id = uuid.uuid4(), uuid.uuid4()

    with engine.begin() as db:
        db.execute(text("insert into categories (id,name,slug,level) values (:id,:name,:name,1)"),
                   {"id": category_id, "name": f"order-test-{category_id}"})
        db.execute(text(
            "insert into products (id,shop_id,category_id,name,name_normalized,price) "
            "values (:id,:shop,:category,'Tên hiện tại','ten hien tai',250000)"
        ), {"id": product_id, "shop": shop_id, "category": category_id})
        db.execute(text(
            "insert into checkouts (id,buyer_id,idempotency_key,request_hash,total_amount) "
            "values (:id,:buyer,:key,:hash,:amount)"
        ), [{"id": id_, "buyer": buyer_id, "key": str(id_), "hash": "0" * 64, "amount": amount}
            for id_, amount in ((checkout_id, 200000), (another_checkout_id, 100000))])
        db.execute(text(
            "insert into orders (id,checkout_id,buyer_id,shop_id,status,total_amount,"
            " shipping_name,shipping_phone,shipping_address,paid_at,created_at) "
            "values (:id,:checkout,:buyer,:shop,'paid',100000,'Recipient','0900000000','Test address',now(),now())"
        ), [
            {"id": order_id, "checkout": checkout_id, "buyer": buyer_id, "shop": shop_id},
            {"id": second_id, "checkout": another_checkout_id, "buyer": buyer_id, "shop": shop_id},
            {"id": sibling_id, "checkout": checkout_id, "buyer": buyer_id, "shop": other_shop_id},
        ])
        db.execute(text(
            "insert into order_items (id,order_id,product_id,product_name,unit_price,quantity,line_total) "
            "values (:id,:order,:product,'Tên lúc mua',50000,2,100000)"
        ), {"id": uuid.uuid4(), "order": order_id, "product": product_id})
        db.execute(text(
            "insert into payments (id,checkout_id,buyer_id,status,amount,refunded_amount,paid_at) "
            "values (:id,:checkout,:buyer,'succeeded',:amount,:refunded,now())"
        ), [
            {"id": payment_id, "checkout": checkout_id, "buyer": buyer_id, "amount": 200000, "refunded": 0},
            {"id": refunded_payment_id, "checkout": another_checkout_id, "buyer": buyer_id, "amount": 100000, "refunded": 100000},
        ])
        db.execute(text(
            "insert into payment_allocations (id,payment_id,order_id,amount,status,refunded_at) "
            "values (:id,:payment,:order,100000,:status,case when :status = 'refunded' then now() else null end)"
        ), [{"id": uuid.uuid4(), "payment": payment, "order": order, "status": status}
            for order, payment, status in (
                (order_id, payment_id, "captured"), (sibling_id, payment_id, "captured"),
                (second_id, refunded_payment_id, "refunded"),
            )])

    try:
        shop_orders = "/api/v1/shops/me/orders"
        detail = f"/api/v1/orders/{order_id}"
        first = client.get(shop_orders, headers=owner, params={"status": "paid", "limit": 1})
        assert first.status_code == 200 and first.headers["cache-control"] == "no-store"
        page = first.json()
        assert len(page["items"]) == 1 and page["next_cursor"]
        following = client.get(shop_orders, headers=owner, params={"status": "paid", "limit": 1, "cursor": page["next_cursor"]}).json()
        assert {page["items"][0]["id"], following["items"][0]["id"]} == {str(order_id), str(second_id)}
        assert following["next_cursor"] is None
        assert client.get(shop_orders, headers=owner, params={"cursor": "wrong"}).status_code == 400
        assert client.get(shop_orders, headers=buyer).status_code == 403
        assert client.get(detail, headers=other).status_code == 403
        assert client.post(f"{detail}/shipment", headers=other).status_code == 403
        assert client.post(f"{detail}/shipment", headers=buyer).status_code == 403
        assert client.post(f"{detail}/completion", headers=owner).status_code == 409
        stats = client.get("/api/v1/shops/me/statistics", headers=owner).json()
        assert stats["total_orders"] == 2 and stats["orders_by_status"]["paid"] == 2
        assert stats["captured_orders"] == 1 and stats["recorded_revenue_vnd"] == "100000"
        other_stats = client.get("/api/v1/shops/me/statistics", headers=other).json()
        assert other_stats["total_orders"] == 1 and other_stats["recorded_revenue_vnd"] == "100000"

        order = client.get(detail, headers=buyer).json()
        assert order["items"][0]["product_name"] == "Tên lúc mua"
        assert order["items"][0]["unit_price"] == 50000 and order["items"][0]["quantity"] == 2
        with ThreadPoolExecutor(max_workers=2) as executor:
            attempts = list(executor.map(lambda _: client.post(f"{detail}/shipment", headers=owner), range(2)))
        assert sorted(response.status_code for response in attempts) == [200, 409]
        shipping = next(response.json() for response in attempts if response.status_code == 200)
        assert shipping["status"] == "shipping" and shipping["shipped_at"]
        done = client.post(f"{detail}/completion", headers=owner)
        assert done.status_code == 200 and done.json()["status"] == "completed"
        assert done.json()["shipped_at"] == shipping["shipped_at"] and done.json()["completed_at"]
        assert client.get(detail, headers=buyer).json()["status"] == "completed"
        current = client.get("/api/v1/shops/me/statistics", headers=owner).json()
        assert current["orders_by_status"]["completed"] == 1 and current["recorded_revenue_vnd"] == "100000"
        assert client.get(f"/api/v1/orders/{sibling_id}", headers=other).json()["status"] == "paid"
        assert client.post(f"{detail}/completion", headers=owner).status_code == 409
    finally:
        with engine.begin() as db:
            db.execute(text("delete from payment_allocations where payment_id in (:first,:second)"),
                       {"first": payment_id, "second": refunded_payment_id})
            db.execute(text("delete from payments where id in (:first,:second)"),
                       {"first": payment_id, "second": refunded_payment_id})
            db.execute(text("delete from orders where checkout_id in (:first,:second)"),
                       {"first": checkout_id, "second": another_checkout_id})
            db.execute(text("delete from checkouts where id in (:first,:second)"),
                       {"first": checkout_id, "second": another_checkout_id})
            db.execute(text("delete from products where id=:id"), {"id": product_id})
            db.execute(text("delete from categories where id=:id"), {"id": category_id})


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
