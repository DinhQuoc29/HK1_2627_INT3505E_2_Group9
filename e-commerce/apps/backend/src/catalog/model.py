"""Entity của Catalog: tỉnh/thành, cửa hàng, danh mục và sản phẩm."""

import uuid
from decimal import Decimal
from enum import Enum

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db import Base, CreatedAtMixin, TimestampMixin, new_id
from orders.model import Inventory


class ProductStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class Province(Base):
    __tablename__ = "provinces"

    code: Mapped[str] = mapped_column(String(4), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)


class Shop(Base, TimestampMixin):
    __tablename__ = "shops"
    __table_args__ = (Index("ix_shops_province_code", "province_code"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_id)
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False, unique=True,
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    province_code: Mapped[str] = mapped_column(
        String(4), ForeignKey("provinces.code", ondelete="RESTRICT"), nullable=False
    )

    province: Mapped[Province] = relationship()


class Category(Base, TimestampMixin):
    """Danh mục hai cấp, với parent_id rỗng ở danh mục gốc."""

    __tablename__ = "categories"
    __table_args__ = (
        CheckConstraint("level IN (1, 2)"),
        CheckConstraint("(parent_id IS NULL) = (level = 1)", name="ck_categories_level_parent"),
        UniqueConstraint(
            "parent_id", "name", name="uq_categories_parent_name",
            postgresql_nulls_not_distinct=True,
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_id)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id", ondelete="RESTRICT")
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    level: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    parent: Mapped["Category | None"] = relationship(remote_side=[id], back_populates="children")
    children: Mapped[list["Category"]] = relationship(
        back_populates="parent", passive_deletes="all"
    )


class Product(Base, TimestampMixin):
    """Một listing của cửa hàng, với giá VND lưu dưới dạng số nguyên."""

    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("price > 0"),
        CheckConstraint("status IN ('active', 'inactive')"),
        CheckConstraint("rating_avg BETWEEN 0 AND 5"),
        CheckConstraint("rating_count >= 0"),
        Index("ix_products_shop_id", "shop_id"),
        Index("ix_products_category_id", "category_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_id)
    shop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shops.id", ondelete="RESTRICT"), nullable=False
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False
    )
    brand: Mapped[str | None] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_normalized: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    price: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(
        Text, nullable=False, default=ProductStatus.ACTIVE.value,
        server_default=ProductStatus.ACTIVE.value,
    )
    rating_avg: Mapped[Decimal] = mapped_column(
        Numeric(3, 2), nullable=False, default=Decimal("0.00"), server_default="0"
    )
    rating_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    shop: Mapped[Shop] = relationship()
    category: Mapped[Category] = relationship()
    images: Mapped[list["ProductImage"]] = relationship(
        back_populates="product",
        order_by="ProductImage.position",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    inventory: Mapped[Inventory | None] = relationship(passive_deletes="all")


class ProductImage(Base, CreatedAtMixin):
    __tablename__ = "product_images"
    __table_args__ = (
        CheckConstraint("position >= 0"),
        UniqueConstraint("product_id", "position", name="uq_product_images_product_position"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_id)
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    position: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0, server_default="0")

    product: Mapped[Product] = relationship(back_populates="images")
