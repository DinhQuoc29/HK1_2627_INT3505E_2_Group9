"""Dữ liệu đơn hàng dựa trên thông tin đã lưu khi đặt đơn."""
import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

from orders.model import OrderStatus
from orders.payments.model import AllocationStatus, PaymentStatus


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
    refunded_amount: int = 0


class OrderPage(BaseModel):
    items: list[OrderOut]
    next_cursor: str | None = None


class ShopStatistics(BaseModel):
    total_orders: int
    orders_by_status: dict[OrderStatus, int]
    captured_orders: int
    recorded_revenue_vnd: str


MAX_CHECKOUT_AMOUNT = 9_007_199_254_740_991  # Giới hạn số nguyên VND biểu diễn chính xác trên web.
ShippingText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, pattern=r"^[^\x00]+$")]


class CheckoutShipping(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: ShippingText = Field(max_length=100)
    phone: ShippingText = Field(max_length=20, pattern=r"^[0-9+(). -]+$")
    address: ShippingText = Field(max_length=500)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, phone: str) -> str:
        if not 8 <= sum(c.isdigit() for c in phone) <= 15:
            raise ValueError("Số điện thoại phải có từ 8 đến 15 chữ số.")
        return phone


class CheckoutItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: uuid.UUID
    quantity: int = Field(strict=True, ge=1, le=2_147_483_647)
    expected_unit_price: int = Field(strict=True, ge=1, le=MAX_CHECKOUT_AMOUNT)


class CheckoutRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[CheckoutItem] = Field(min_length=1)
    shipping: CheckoutShipping
    simulate: Literal["succeeded", "failed"] = "succeeded"

    @field_validator("items")
    @classmethod
    def unique_products(cls, items: list[CheckoutItem]) -> list[CheckoutItem]:
        if len({item.product_id for item in items}) != len(items):
            raise ValueError("Mỗi sản phẩm chỉ được xuất hiện một lần.")
        return items


class PaymentAllocationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    order_id: uuid.UUID
    amount: int
    status: AllocationStatus
    refunded_at: datetime | None


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    checkout_id: uuid.UUID
    method: Literal["simulated"]
    status: PaymentStatus
    amount: int
    refunded_amount: int
    attempt_count: int
    paid_at: datetime | None
    allocations: list[PaymentAllocationOut]


class CheckoutOut(BaseModel):
    id: uuid.UUID
    total_amount: int
    created_at: datetime
    orders: list[OrderOut]
    payment: PaymentOut
