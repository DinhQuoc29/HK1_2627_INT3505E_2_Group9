-- Initial commerce schema for PostgreSQL 16. UUIDs are assigned by the application.

BEGIN;

CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(100),
    full_name VARCHAR(100) NOT NULL,
    role TEXT NOT NULL DEFAULT 'buyer' CHECK (role IN ('buyer', 'seller', 'admin')),
    failed_login_count SMALLINT NOT NULL DEFAULT 0 CHECK (failed_login_count >= 0),
    locked_until TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_users_email_lower CHECK (email = lower(email))
);

CREATE TABLE user_identities (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider TEXT NOT NULL CHECK (provider IN ('google')),
    provider_subject VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_user_identities_provider_subject UNIQUE (provider, provider_subject),
    CONSTRAINT uq_user_identities_user_provider UNIQUE (user_id, provider)
);

CREATE TABLE auth_sessions (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    refresh_token_hash CHAR(64) NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE provinces (
    code VARCHAR(4) PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE shops (
    id UUID PRIMARY KEY,
    owner_user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE RESTRICT,
    name VARCHAR(150) NOT NULL,
    province_code VARCHAR(4) NOT NULL REFERENCES provinces(code) ON DELETE RESTRICT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE categories (
    id UUID PRIMARY KEY,
    parent_id UUID REFERENCES categories(id) ON DELETE RESTRICT,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(120) NOT NULL UNIQUE,
    level SMALLINT NOT NULL CHECK (level IN (1, 2)),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_categories_level_parent CHECK ((parent_id IS NULL) = (level = 1)),
    CONSTRAINT uq_categories_parent_name UNIQUE NULLS NOT DISTINCT (parent_id, name)
);

CREATE TABLE products (
    id UUID PRIMARY KEY,
    shop_id UUID NOT NULL REFERENCES shops(id) ON DELETE RESTRICT,
    category_id UUID NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
    brand VARCHAR(100),
    name VARCHAR(255) NOT NULL,
    name_normalized VARCHAR(255) NOT NULL,
    description TEXT,
    price BIGINT NOT NULL CHECK (price > 0),
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
    rating_avg NUMERIC(3,2) NOT NULL DEFAULT 0 CHECK (rating_avg BETWEEN 0 AND 5),
    rating_count INTEGER NOT NULL DEFAULT 0 CHECK (rating_count >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE product_images (
    id UUID PRIMARY KEY,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    url VARCHAR(500) NOT NULL,
    position SMALLINT NOT NULL DEFAULT 0 CHECK (position >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_product_images_product_position UNIQUE (product_id, position)
);

CREATE TABLE cart_items (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price_at_add BIGINT NOT NULL CHECK (unit_price_at_add > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT pk_cart_items PRIMARY KEY (user_id, product_id)
);

CREATE TABLE inventories (
    product_id UUID PRIMARY KEY REFERENCES products(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE checkouts (
    id UUID PRIMARY KEY,
    buyer_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    idempotency_key VARCHAR(64) NOT NULL,
    request_hash CHAR(64) NOT NULL,
    total_amount BIGINT NOT NULL CHECK (total_amount >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_checkouts_buyer_key UNIQUE (buyer_id, idempotency_key)
);

CREATE TABLE orders (
    id UUID PRIMARY KEY,
    checkout_id UUID NOT NULL REFERENCES checkouts(id) ON DELETE RESTRICT,
    buyer_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    shop_id UUID NOT NULL REFERENCES shops(id) ON DELETE RESTRICT,
    status TEXT NOT NULL DEFAULT 'pending_payment' CHECK (status IN ('pending_payment', 'paid', 'shipping', 'completed', 'cancelled')),
    total_amount BIGINT NOT NULL CHECK (total_amount >= 0),
    shipping_name VARCHAR(100) NOT NULL,
    shipping_phone VARCHAR(20) NOT NULL,
    shipping_address VARCHAR(500) NOT NULL,
    paid_at TIMESTAMPTZ,
    shipped_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    cancelled_at TIMESTAMPTZ,
    cancelled_by TEXT CHECK (cancelled_by IN ('buyer', 'seller')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_orders_checkout_shop UNIQUE (checkout_id, shop_id),
    CONSTRAINT ck_orders_cancel_fields CHECK ((status = 'cancelled' AND cancelled_at IS NOT NULL AND cancelled_by IS NOT NULL) OR (status <> 'cancelled' AND cancelled_at IS NULL AND cancelled_by IS NULL)),
    CONSTRAINT ck_orders_paid_at CHECK (status NOT IN ('paid', 'shipping', 'completed') OR paid_at IS NOT NULL),
    CONSTRAINT ck_orders_shipped_at CHECK (status NOT IN ('shipping', 'completed') OR shipped_at IS NOT NULL),
    CONSTRAINT ck_orders_completed_at CHECK ((status = 'completed') = (completed_at IS NOT NULL))
);

CREATE TABLE order_items (
    id UUID PRIMARY KEY,
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    product_name VARCHAR(255) NOT NULL,
    unit_price BIGINT NOT NULL CHECK (unit_price > 0),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    line_total BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_order_items_line_total CHECK (line_total = unit_price * quantity),
    CONSTRAINT uq_order_items_order_product UNIQUE (order_id, product_id)
);

CREATE TABLE payments (
    id UUID PRIMARY KEY,
    checkout_id UUID NOT NULL UNIQUE REFERENCES checkouts(id) ON DELETE RESTRICT,
    buyer_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    method TEXT NOT NULL DEFAULT 'simulated' CHECK (method IN ('simulated')),
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'succeeded', 'failed', 'cancelled')),
    amount BIGINT NOT NULL DEFAULT 0 CHECK (amount >= 0),
    refunded_amount BIGINT NOT NULL DEFAULT 0,
    attempt_count SMALLINT NOT NULL DEFAULT 0 CHECK (attempt_count >= 0),
    paid_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_payments_refund_range CHECK (refunded_amount BETWEEN 0 AND amount),
    CONSTRAINT ck_payments_paid_at CHECK ((status = 'succeeded') = (paid_at IS NOT NULL))
);

CREATE TABLE payment_allocations (
    id UUID PRIMARY KEY,
    payment_id UUID NOT NULL REFERENCES payments(id) ON DELETE RESTRICT,
    order_id UUID NOT NULL UNIQUE REFERENCES orders(id) ON DELETE RESTRICT,
    amount BIGINT NOT NULL CHECK (amount >= 0),
    status TEXT NOT NULL DEFAULT 'captured' CHECK (status IN ('captured', 'refunded')),
    refunded_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_payment_allocations_refund CHECK ((status = 'refunded') = (refunded_at IS NOT NULL))
);

CREATE TABLE reviews (
    id UUID PRIMARY KEY,
    order_item_id UUID NOT NULL UNIQUE REFERENCES order_items(id) ON DELETE RESTRICT,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    rating SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    content TEXT CHECK (char_length(content) <= 2000),
    status TEXT NOT NULL DEFAULT 'visible' CHECK (status IN ('visible', 'hidden')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ix_auth_sessions_user_id ON auth_sessions (user_id);
CREATE INDEX ix_shops_province_code ON shops (province_code);
CREATE INDEX ix_products_shop_id ON products (shop_id);
CREATE INDEX ix_products_category_id ON products (category_id);
CREATE INDEX ix_cart_items_product_id ON cart_items (product_id);
CREATE INDEX ix_orders_buyer_id ON orders (buyer_id);
CREATE INDEX ix_orders_shop_id ON orders (shop_id);
CREATE INDEX ix_order_items_product_id ON order_items (product_id);
CREATE INDEX ix_payments_buyer_id ON payments (buyer_id);
CREATE INDEX ix_payment_allocations_payment_id ON payment_allocations (payment_id);
CREATE INDEX ix_reviews_product_id ON reviews (product_id);
CREATE INDEX ix_reviews_user_id ON reviews (user_id);

-- Provincial codes from Decision 19/2025/QD-TTg, Appendix I.
INSERT INTO provinces (code, name) VALUES
    ('01', 'Hà Nội'),
    ('04', 'Cao Bằng'),
    ('08', 'Tuyên Quang'),
    ('11', 'Điện Biên'),
    ('12', 'Lai Châu'),
    ('14', 'Sơn La'),
    ('15', 'Lào Cai'),
    ('19', 'Thái Nguyên'),
    ('20', 'Lạng Sơn'),
    ('22', 'Quảng Ninh'),
    ('24', 'Bắc Ninh'),
    ('25', 'Phú Thọ'),
    ('31', 'Hải Phòng'),
    ('33', 'Hưng Yên'),
    ('37', 'Ninh Bình'),
    ('38', 'Thanh Hóa'),
    ('40', 'Nghệ An'),
    ('42', 'Hà Tĩnh'),
    ('44', 'Quảng Trị'),
    ('46', 'Huế'),
    ('48', 'Đà Nẵng'),
    ('51', 'Quảng Ngãi'),
    ('52', 'Gia Lai'),
    ('56', 'Khánh Hòa'),
    ('66', 'Đắk Lắk'),
    ('68', 'Lâm Đồng'),
    ('75', 'Đồng Nai'),
    ('79', 'Hồ Chí Minh'),
    ('80', 'Tây Ninh'),
    ('82', 'Đồng Tháp'),
    ('86', 'Vĩnh Long'),
    ('91', 'An Giang'),
    ('92', 'Cần Thơ'),
    ('96', 'Cà Mau');

COMMIT;
