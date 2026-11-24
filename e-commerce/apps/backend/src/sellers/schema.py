"""Schema (Pydantic) của Sellers."""
import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

from catalog.schema import CreateShopRequest


class ApplyRequest(CreateShopRequest):
    """Hồ sơ xin mở shop: cùng quy tắc tên shop và tỉnh/thành như Shop."""


class RejectRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str

    @field_validator("reason", mode="before")
    @classmethod
    def _reason(cls, v):
        if not isinstance(v, str):
            raise ValueError("Lý do không hợp lệ.")
        v = v.strip()
        if not 3 <= len(v) <= 500:
            raise ValueError("Lý do từ 3 đến 500 ký tự.")
        return v


class ApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    shop_name: str
    province_code: str
    province_name: str
    status: Literal["pending", "approved", "rejected"]
    reject_reason: str | None = None
    created_at: datetime
    reviewed_at: datetime | None = None


class AdminApplicationOut(ApplicationOut):
    applicant_id: uuid.UUID
    applicant_email: str
    applicant_name: str


class AdminApplicationPage(BaseModel):
    items: list[AdminApplicationOut]
    next_cursor: str | None = None
