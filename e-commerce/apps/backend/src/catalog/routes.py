"""Endpoint Catalog (/api/v1): tỉnh/thành, gian hàng và sản phẩm của seller."""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response

from accounts.authentication import CurrentAuth
from accounts.permissions import require_role
from catalog import categories, listings, repository, shops
from catalog.schema import (
    CreateShopRequest, ProductCategoryOut, ProductInput, ProductState, ProductStatusRequest, ProvinceOut, SellerProductOut,
    SellerProductPage, ShopOut,
)
from db import session_scope

router = APIRouter(prefix="/api/v1")
SellerAuth = Annotated[CurrentAuth, Depends(require_role("seller"))]


@router.get("/provinces", response_model=list[ProvinceOut])
def list_provinces():
    with session_scope() as s:
        return [ProvinceOut.model_validate(p) for p in repository.list_provinces(s)]


@router.get("/shops/me", response_model=ShopOut)
def get_my_shop(response: Response, auth: SellerAuth):
    with session_scope() as s:
        out = ShopOut.model_validate(shops.my_shop(s, auth.user.id))
    response.headers["Cache-Control"] = "no-store"
    return out


@router.put("/shops/me", response_model=ShopOut)
def update_my_shop(body: CreateShopRequest, response: Response, auth: SellerAuth):
    response.headers["Cache-Control"] = "no-store"
    with session_scope() as s:
        shop = shops.update_my_shop(s, auth.user.id, name=body.name, province_code=body.province_code)
        return ShopOut.model_validate(shop)


@router.get("/shops/me/product-categories", response_model=list[ProductCategoryOut])
def list_product_categories(response: Response, auth: SellerAuth):
    response.headers["Cache-Control"] = "no-store"
    with session_scope() as s:
        shops.my_shop(s, auth.user.id)
        return categories.product_categories(s)


@router.get("/shops/me/products", response_model=SellerProductPage)
def list_my_products(
    response: Response, auth: SellerAuth, q: str = Query("", max_length=255, pattern=r"^[^\x00]*$"),
    status: ProductState | None = None, page: int = Query(1, ge=1, le=100_000), limit: int = Query(12, ge=1, le=50),
):
    response.headers["Cache-Control"] = "no-store"
    with session_scope() as s:
        return listings.list_products(s, shops.my_shop(s, auth.user.id).id, q=q, status=status, page=page, limit=limit)


@router.post("/shops/me/products", status_code=201, response_model=SellerProductOut)
def create_my_product(body: ProductInput, response: Response, auth: SellerAuth):
    response.headers["Cache-Control"] = "no-store"
    with session_scope() as s:
        return listings.create_product(s, shops.my_shop(s, auth.user.id).id, body)


@router.put("/shops/me/products/{product_id}", response_model=SellerProductOut)
def update_my_product(product_id: uuid.UUID, body: ProductInput, response: Response, auth: SellerAuth):
    response.headers["Cache-Control"] = "no-store"
    with session_scope() as s:
        return listings.update_product(s, shops.my_shop(s, auth.user.id).id, product_id, body)


@router.patch("/shops/me/products/{product_id}/status", response_model=SellerProductOut)
def change_my_product_status(product_id: uuid.UUID, body: ProductStatusRequest, response: Response, auth: SellerAuth):
    response.headers["Cache-Control"] = "no-store"
    with session_scope() as s:
        return listings.set_product_status(s, shops.my_shop(s, auth.user.id).id, product_id, body.status)
