"""Schema (Pydantic) cho request/response của Catalog (hiện có: Shops, Provinces)."""
import uuid
from datetime import datetime
from typing import Annotated, Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator


class CreateShopRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    province_code: str

    @field_validator("name", mode="before")
    @classmethod
    def _name(cls, v):
        if not isinstance(v, str):
            raise ValueError("Tên shop không hợp lệ.")
        v = " ".join(v.split())
        if not 3 <= len(v) <= 150:
            raise ValueError("Tên shop từ 3 đến 150 ký tự.")
        return v

    @field_validator("province_code", mode="before")
    @classmethod
    def _province(cls, v):
        if not isinstance(v, str) or not 1 <= len(v.strip()) <= 4:
            raise ValueError("Mã tỉnh/thành không hợp lệ.")
        return v.strip()


class ProvinceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    name: str


class ShopOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    province: ProvinceOut
    created_at: datetime


class ProductCategoryOut(BaseModel):
    id: uuid.UUID
    name: str
    parent_name: str


ProductState = Literal["active", "inactive"]
ImageUrl = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]


class ProductInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=255)
    brand: str | None = Field(default=None, max_length=100)
    description: str = Field(min_length=1, max_length=5000)
    category_id: uuid.UUID
    price: int = Field(strict=True, ge=1, le=9_007_199_254_740_991)
    quantity: int = Field(strict=True, ge=0, le=2_147_483_647)
    images: list[ImageUrl] = Field(min_length=1, max_length=8)

    @field_validator("name", "brand", "description")
    @classmethod
    def _valid_text(cls, value: str | None) -> str | None:
        if value is not None and "\x00" in value:
            raise ValueError("Không được chứa ký tự rỗng.")
        return value

    @field_validator("images")
    @classmethod
    def _valid_images(cls, images: list[str]) -> list[str]:
        for url in images:
            try:
                parts = urlsplit(url)
                port = parts.port
                valid = (
                    parts.scheme in ("http", "https") and parts.hostname and parts.username is None
                    and parts.password is None and not any(c.isspace() or ord(c) < 32 for c in url)
                    and (port is None or port > 0) and "\\" not in url
                )
            except ValueError:
                valid = False
            if not valid:
                raise ValueError("Link ảnh phải là URL HTTP hoặc HTTPS hợp lệ, không chứa thông tin đăng nhập.")
        return images


class ProductStatusRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: ProductState


class SellerProductOut(BaseModel):
    id: uuid.UUID
    name: str
    brand: str | None
    description: str | None
    category_id: uuid.UUID
    category_name: str
    price: int
    quantity: int
    images: list[str]
    status: ProductState


class SellerProductPage(BaseModel):
    items: list[SellerProductOut]
    has_more: bool
