"""Ghi số lượng tồn kho tuyệt đối khi người bán cập nhật sản phẩm."""
import uuid

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from orders.model import Inventory


def put_quantity(s: Session, product_id: uuid.UUID, quantity: int) -> None:
    stmt = insert(Inventory).values(product_id=product_id, quantity=quantity)
    s.execute(stmt.on_conflict_do_update(
        index_elements=[Inventory.product_id],
        set_={"quantity": stmt.excluded.quantity, "updated_at": func.now()},
        where=Inventory.quantity != stmt.excluded.quantity,
    ))
