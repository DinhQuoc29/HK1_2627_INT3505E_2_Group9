"""Entity thanh toán (giả lập): payments, payment_allocations."""
import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db import Base, CreatedAtMixin, TimestampMixin, new_id


class PaymentStatus(str, Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AllocationStatus(str, Enum):
    CAPTURED = "captured"
    REFUNDED = "refunded"


class Payment(Base, TimestampMixin):
    """Một payment giả lập cho mỗi checkout (UNIQUE checkout_id chống trả trùng)."""

    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint("method IN ('simulated')", name="ck_payments_method"),
        CheckConstraint(
            "status IN ('pending','succeeded','failed','cancelled')", name="ck_payments_status"
        ),
        CheckConstraint("amount >= 0", name="ck_payments_amount"),
        CheckConstraint("attempt_count >= 0", name="ck_payments_attempt_count"),
        CheckConstraint("refunded_amount BETWEEN 0 AND amount", name="ck_payments_refund_range"),
        CheckConstraint("(status = 'succeeded') = (paid_at IS NOT NULL)", name="ck_payments_paid_at"),
        Index("ix_payments_buyer_id", "buyer_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_id)
    checkout_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("checkouts.id", ondelete="RESTRICT"),
        nullable=False, unique=True,
    )
    buyer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    method: Mapped[str] = mapped_column(Text, nullable=False, default="simulated", server_default="simulated")
    status: Mapped[str] = mapped_column(
        Text, nullable=False, default=PaymentStatus.PENDING.value,
        server_default=PaymentStatus.PENDING.value,
    )
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, server_default="0")
    refunded_amount: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, server_default="0")
    attempt_count: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0, server_default="0")
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    allocations: Mapped[list["PaymentAllocation"]] = relationship(back_populates="payment")


class PaymentAllocation(Base, CreatedAtMixin):
    """Phân bổ tiền của payment cho từng order (mỗi order thu một lần)."""

    __tablename__ = "payment_allocations"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_payment_allocations_amount"),
        CheckConstraint("status IN ('captured','refunded')", name="ck_payment_allocations_status"),
        CheckConstraint(
            "(status = 'refunded') = (refunded_at IS NOT NULL)", name="ck_payment_allocations_refund"
        ),
        Index("ix_payment_allocations_payment_id", "payment_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_id)
    payment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("payments.id", ondelete="RESTRICT"), nullable=False
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="RESTRICT"),
        nullable=False, unique=True,
    )
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(
        Text, nullable=False, default=AllocationStatus.CAPTURED.value,
        server_default=AllocationStatus.CAPTURED.value,
    )
    refunded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    payment: Mapped[Payment] = relationship(back_populates="allocations")
