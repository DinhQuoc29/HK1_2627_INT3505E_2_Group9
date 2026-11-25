"""Đọc đơn hàng và cập nhật giao hàng bằng quyền người bán."""
import base64
import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response

from accounts.authentication import CurrentAuth
from accounts.model import Role
from accounts.permissions import require_role
from catalog.shops import my_shop
from common.errors import ProblemError
from db import session_scope
from orders import fulfillment, repository, statistics
from orders.model import OrderStatus
from orders.schema import OrderOut, OrderPage, ShopStatistics

router = APIRouter(prefix="/api/v1")
SellerAuth = Annotated[CurrentAuth, Depends(require_role("seller"))]
OrderReader = Annotated[CurrentAuth, Depends(require_role("buyer", "seller"))]


@router.get("/shops/me/statistics", response_model=ShopStatistics)
def get_my_shop_statistics(response: Response, auth: SellerAuth):
    response.headers["Cache-Control"] = "no-store"
    with session_scope() as s:
        shop = my_shop(s, auth.user.id)
        return statistics.for_shop(s, shop.id)


def _encode_cursor(created_at: datetime, order_id: uuid.UUID) -> str:
    return base64.urlsafe_b64encode(f"{created_at.isoformat()}|{order_id}".encode()).decode()


def _decode_cursor(cursor: str) -> tuple[datetime, uuid.UUID]:
    try:
        raw = base64.b64decode(cursor.encode("ascii"), altchars=b"-_", validate=True).decode("ascii")
        timestamp, order_id = raw.split("|")
        created_at = datetime.fromisoformat(timestamp)
        if created_at.utcoffset() is None:
            raise ValueError("Cursor requires a timezone")
        return created_at, uuid.UUID(order_id)
    except ValueError as exc:
        raise ProblemError(400, "invalid-cursor", "Con trỏ đơn hàng không hợp lệ.") from exc


@router.get("/shops/me/orders", response_model=OrderPage)
def list_my_shop_orders(
    response: Response, auth: SellerAuth, status: OrderStatus | None = None,
    limit: int = Query(20, ge=1, le=100), cursor: str | None = Query(None, max_length=200),
):
    after = _decode_cursor(cursor) if cursor is not None else None
    response.headers["Cache-Control"] = "no-store"
    with session_scope() as s:
        shop = my_shop(s, auth.user.id)
        rows = repository.list_shop_orders(s, shop.id, status=status, after=after, limit=limit)
        last = rows[limit - 1] if len(rows) > limit else None
        return OrderPage(
            items=repository.describe_orders(s, rows[:limit], shop),
            next_cursor=_encode_cursor(last.created_at, last.id) if last is not None else None,
        )


@router.get("/orders/{order_id}", response_model=OrderOut)
def get_order(order_id: uuid.UUID, response: Response, auth: OrderReader):
    response.headers["Cache-Control"] = "no-store"
    with session_scope() as s:
        found = repository.find_order(s, order_id)
        if found is None:
            raise ProblemError(404, "order-not-found", "Không tìm thấy đơn hàng.")
        order, shop = found
        owns_shop = auth.user.role == Role.SELLER.value and shop.owner_user_id == auth.user.id
        if not owns_shop and order.buyer_id != auth.user.id:
            raise ProblemError(403, "forbidden", "Bạn không có quyền xem đơn hàng này.")
        return repository.describe_orders(s, [order], shop)[0]


@router.post("/orders/{order_id}/shipment", response_model=OrderOut)
def record_shipment(order_id: uuid.UUID, response: Response, auth: SellerAuth):
    response.headers["Cache-Control"] = "no-store"
    with session_scope() as s:
        return fulfillment.advance(s, order_id, auth.user.id, OrderStatus.SHIPPING)


@router.post("/orders/{order_id}/completion", response_model=OrderOut)
def complete_delivery(order_id: uuid.UUID, response: Response, auth: SellerAuth):
    response.headers["Cache-Control"] = "no-store"
    with session_scope() as s:
        return fulfillment.advance(s, order_id, auth.user.id, OrderStatus.COMPLETED)
