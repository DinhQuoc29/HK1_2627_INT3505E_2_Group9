import uuid
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from catalog.schema import CatalogShop


class CartQuantity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    quantity: Annotated[int, Field(strict=True, ge=1, le=2_147_483_647)]


class AddCartItem(CartQuantity):
    product_id: uuid.UUID


class CartLine(BaseModel):
    product_id: uuid.UUID
    name: str
    image_url: str | None
    quantity: int
    is_active: bool
    available_quantity: int
    price_changed: bool
    unit_price_vnd: str
    line_total_vnd: str


class CartGroup(BaseModel):
    shop: CatalogShop
    items: list[CartLine]
    subtotal_vnd: str


class CartOut(BaseModel):
    groups: list[CartGroup]
    subtotal_vnd: str
