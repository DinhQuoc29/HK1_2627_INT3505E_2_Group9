import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response

from accounts.authentication import CurrentAuth
from accounts.permissions import require_role
from cart import repository, service
from cart.schema import AddCartItem, CartOut, CartQuantity
from db import session_scope

router = APIRouter(prefix="/api/v1/cart")
BuyerAuth = Annotated[CurrentAuth, Depends(require_role("buyer"))]


@router.get("", response_model=CartOut)
def get_cart(response: Response, auth: BuyerAuth):
    response.headers["Cache-Control"] = "no-store"
    with session_scope() as s:
        return service.get_cart(s, auth.user.id)


@router.post("/items", response_model=CartOut)
def add_cart_item(body: AddCartItem, response: Response, auth: BuyerAuth):
    response.headers["Cache-Control"] = "no-store"
    with session_scope() as s:
        repository.lock_buyer_cart(s, auth.user.id)
        service.add_item(s, auth.user.id, body.product_id, body.quantity)
        return service.get_cart(s, auth.user.id)


@router.patch("/items/{product_id}", response_model=CartOut)
def change_cart_item(product_id: uuid.UUID, body: CartQuantity, response: Response, auth: BuyerAuth):
    response.headers["Cache-Control"] = "no-store"
    with session_scope() as s:
        repository.lock_buyer_cart(s, auth.user.id)
        service.set_quantity(s, auth.user.id, product_id, body.quantity)
        return service.get_cart(s, auth.user.id)


@router.delete("/items/{product_id}", response_model=CartOut)
def remove_cart_item(product_id: uuid.UUID, response: Response, auth: BuyerAuth):
    response.headers["Cache-Control"] = "no-store"
    with session_scope() as s:
        repository.lock_buyer_cart(s, auth.user.id)
        repository.remove_item(s, auth.user.id, product_id)
        return service.get_cart(s, auth.user.id)
