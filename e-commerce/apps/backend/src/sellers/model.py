"""Entity của module Sellers: seller_applications (hồ sơ xin mở shop, admin duyệt)."""
import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from db import Base, TimestampMixin, new_id


class ApplicationStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class SellerApplication(Base, TimestampMixin):
    __tablename__ = "seller_applications"
    __table_args__ = (
        CheckConstraint("status IN ('pending','approved','rejected')", name="ck_seller_applications_status"),
        Index("uq_seller_applications_pending_user", "user_id", unique=True, postgresql_where=text("status = 'pending'")),
        Index("ix_seller_applications_status_created", "status", "created_at", "id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_id)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    shop_name: Mapped[str] = mapped_column(String(150), nullable=False)
    province_code: Mapped[str] = mapped_column(
        String(4), ForeignKey("provinces.code", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        Text, nullable=False, default=ApplicationStatus.PENDING.value, server_default=ApplicationStatus.PENDING.value
    )
    reject_reason: Mapped[str | None] = mapped_column(String(500))
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
