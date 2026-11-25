"""Truy cập dữ liệu Catalog. Chỉ module này ghi vào shops (và các bảng catalog khác)."""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from catalog.model import Province, Shop


def list_provinces(s: Session) -> list[Province]:
    return list(s.scalars(select(Province).order_by(Province.name)))


def get_province(s: Session, code: str) -> Province | None:
    return s.get(Province, code)


def get_shop_by_owner(s: Session, owner_user_id: uuid.UUID) -> Shop | None:
    return s.scalar(select(Shop).where(Shop.owner_user_id == owner_user_id))


def add_shop(s: Session, shop: Shop) -> Shop:
    s.add(shop)
    s.flush()
    return shop
