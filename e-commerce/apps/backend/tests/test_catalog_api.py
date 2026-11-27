from contextlib import contextmanager

from fastapi.testclient import TestClient

from accounts.model import User
from app import create_app
from catalog import routes
from catalog.model import Category, Product, Shop
from db import new_id


def test_catalog_combines_categories_and_sorts_before_pagination(session, monkeypatch):
    keyword = new_id().hex
    seller = User(email=f"{keyword}@example.com", full_name="Người bán", role="seller")
    session.add(seller)
    session.flush()
    shop = Shop(owner_user_id=seller.id, name="Shop", province_code="01")
    clothing = Category(name=f"Thời trang {keyword}", slug=f"clothing-{keyword}", level=1)
    decor = Category(name=f"Trang trí {keyword}", slug=f"decor-{keyword}", level=1)
    shoes = Category(name="Giày", slug=f"shoes-{keyword}", level=2, parent=clothing)
    vases = Category(name="Bình", slug=f"vases-{keyword}", level=2, parent=decor)
    lamps = Category(name="Đèn", slug=f"lamps-{keyword}", level=2, parent=decor)
    for category, price in [(shoes, 600), (vases, 300), (shoes, 110), (lamps, 200)]:
        session.add(Product(shop=shop, category=category, name=keyword, name_normalized=keyword, price=price))
    session.flush()

    @contextmanager
    def request_session():
        yield session

    monkeypatch.setattr(routes, "session_scope", request_session)
    params = {"q": keyword, "category": [clothing.slug, shoes.slug, vases.slug], "limit": 2}

    with TestClient(create_app()) as client:
        def browse(**query):
            response = client.get("/api/v1/products", params={**params, **query})
            assert response.status_code == 200
            data = response.json()
            return [product["price"] for product in data["items"]], data["has_more"]

        assert browse(sort="price-asc") == ([110, 300], True)
        assert browse(sort="price-asc", page=2) == ([600], False)
        assert browse(sort="price-desc") == ([600, 300], True)
        assert browse(category=clothing.slug, sort="price-asc") == ([110, 600], False)
        assert client.get("/api/v1/products", params={"category": [clothing.slug, ""]}).status_code == 422
