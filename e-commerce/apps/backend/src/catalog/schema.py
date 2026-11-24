"""Schema (Pydantic) cho request/response của Catalog (hiện có: Shops, Provinces)."""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


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
