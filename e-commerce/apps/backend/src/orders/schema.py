"""Dữ liệu đơn hàng dựa trên thông tin đã lưu khi đặt đơn."""
import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from orders.model import OrderStatus


class OrderShopOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str


class ShippingOut(BaseModel):
    name: str
    phone: str
    address: str


class OrderItemOut(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    product_name: str
    unit_price: int
    quantity: int
    line_total: int
    has_review: bool


class OrderOut(BaseModel):
    id: uuid.UUID
    checkout_id: uuid.UUID
    shop: OrderShopOut
    status: OrderStatus
    total_amount: int
    shipping: ShippingOut
    items: list[OrderItemOut]
    paid_at: datetime | None
    shipped_at: datetime | None
    completed_at: datetime | None
    cancelled_at: datetime | None
    cancelled_by: Literal["buyer", "seller"] | None
    created_at: datetime


class OrderPage(BaseModel):
    items: list[OrderOut]
    next_cursor: str | None = None


class ShopStatistics(BaseModel):
    total_orders: int
    orders_by_status: dict[OrderStatus, int]
    captured_orders: int
    recorded_revenue_vnd: str
