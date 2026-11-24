from datetime import datetime, timezone

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from db import new_id
from orders.model import Checkout, Inventory, Order, OrderItem
from orders.payments.model import Payment, PaymentAllocation
from reviews.model import Review


def _seed_refs(s):
    u, sel, sh, c, p = (new_id() for _ in range(5))
    s.execute(text("insert into users(id,email,full_name) values(:u,:ue,'A'),(:s,:se,'S')"),
              {"u": u, "s": sel, "ue": f"{u}@x.com", "se": f"{sel}@x.com"})
    s.execute(text("insert into shops(id,owner_user_id,name,province_code) values(:h,:s,'Shop','01')"),
              {"h": sh, "s": sel})
    s.execute(text("insert into categories(id,name,slug,level) values(:c,'C',:sl,1)"),
              {"c": c, "sl": str(c)})
    s.execute(text("insert into products(id,shop_id,category_id,name,name_normalized,price) "
                   "values(:p,:h,:c,'P','p',1000)"), {"p": p, "h": sh, "c": c})
    return u, sh, p


def _completed_order(s):
    u, sh, p = _seed_refs(s)
    now = datetime.now(timezone.utc)
    co = Checkout(buyer_id=u, idempotency_key="k", request_hash="a" * 64, total_amount=2000)
    o = Order(checkout=co, buyer_id=u, shop_id=sh, total_amount=2000, shipping_name="n",
              shipping_phone="1", shipping_address="x", status="completed",
              paid_at=now, shipped_at=now, completed_at=now)
    oi = OrderItem(order=o, product_id=p, product_name="P", unit_price=1000, quantity=2, line_total=2000)
    s.add_all([co, o, oi])
    s.flush()
    return u, p, co, o, oi


def test_order_payment_review_roundtrip(session):
    u, p, co, o, oi = _completed_order(session)
    pay = Payment(checkout_id=co.id, buyer_id=u, status="succeeded", amount=2000,
                  paid_at=datetime.now(timezone.utc))
    session.add(pay)
    session.flush()
    session.add(PaymentAllocation(payment_id=pay.id, order_id=o.id, amount=2000))
    session.add(Review(order_item_id=oi.id, product_id=p, user_id=u, rating=5, content="ok"))
    session.flush()


def test_line_total_must_match(session):
    u, sh, p = _seed_refs(session)
    co = Checkout(buyer_id=u, idempotency_key="k", request_hash="a" * 64, total_amount=1)
    o = Order(checkout=co, buyer_id=u, shop_id=sh, total_amount=1, shipping_name="n",
              shipping_phone="1", shipping_address="x")
    session.add(OrderItem(order=o, product_id=p, product_name="P", unit_price=1000,
                          quantity=2, line_total=1))
    with pytest.raises(IntegrityError):
        session.flush()


def test_one_review_per_order_item(session):
    u, p, co, o, oi = _completed_order(session)
    session.add(Review(order_item_id=oi.id, product_id=p, user_id=u, rating=4))
    session.flush()
    session.add(Review(order_item_id=oi.id, product_id=p, user_id=u, rating=3))
    with pytest.raises(IntegrityError):
        session.flush()


def test_inventory_cannot_go_negative(session):
    u, sh, p = _seed_refs(session)
    session.add(Inventory(product_id=p, quantity=5))
    session.flush()
    with pytest.raises(IntegrityError):
        session.execute(text("update inventories set quantity = quantity - 6 where product_id = :p"), {"p": p})
