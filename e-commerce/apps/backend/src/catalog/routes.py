"""Endpoint Catalog (/api/v1): shop của seller và danh sách tỉnh/thành. Shop được tạo khi admin duyệt hồ sơ (sellers)."""
from fastapi import APIRouter, Depends, Response

from accounts.authentication import CurrentAuth, current_auth
from accounts.permissions import require_role
from catalog import repository, shops
from catalog.schema import ProvinceOut, ShopOut
from db import session_scope

router = APIRouter(prefix="/api/v1")


@router.get("/provinces", response_model=list[ProvinceOut])
def list_provinces():
    with session_scope() as s:
        return [ProvinceOut.model_validate(p) for p in repository.list_provinces(s)]


@router.get("/shops/me", response_model=ShopOut)
def get_my_shop(response: Response, auth: CurrentAuth = Depends(require_role("seller"))):
    with session_scope() as s:
        out = ShopOut.model_validate(shops.my_shop(s, auth.user.id))
    response.headers["Cache-Control"] = "no-store"
    return out
