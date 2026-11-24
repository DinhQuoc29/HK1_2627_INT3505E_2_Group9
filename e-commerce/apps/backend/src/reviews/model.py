"""Entity của module Reviews: reviews."""
import uuid
from enum import Enum

from sqlalchemy import CheckConstraint, ForeignKey, Index, SmallInteger, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from db import Base, TimestampMixin, new_id


class ReviewStatus(str, Enum):
    VISIBLE = "visible"
    HIDDEN = "hidden"


class Review(Base, TimestampMixin):
    """Đánh giá sản phẩm đã mua; một review cho mỗi order_item của đơn completed."""

    __tablename__ = "reviews"
    __table_args__ = (
        CheckConstraint("rating BETWEEN 1 AND 5", name="ck_reviews_rating"),
        CheckConstraint("char_length(content) <= 2000", name="ck_reviews_content_len"),
        CheckConstraint("status IN ('visible','hidden')", name="ck_reviews_status"),
        Index("ix_reviews_product_id", "product_id"),
        Index("ix_reviews_user_id", "user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_id)
    order_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("order_items.id", ondelete="RESTRICT"),
        nullable=False, unique=True,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    rating: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    content: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        Text, nullable=False, default=ReviewStatus.VISIBLE.value,
        server_default=ReviewStatus.VISIBLE.value,
    )
