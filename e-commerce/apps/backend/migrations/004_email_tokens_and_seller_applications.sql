-- Xác minh email, quên mật khẩu (email_tokens) và duyệt hồ sơ người bán (seller_applications).
-- Chạy được nhiều lần (idempotent). DB tạo mới chạy 001..004 theo thứ tự tên file.

BEGIN;

ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified_at TIMESTAMPTZ;
-- Tài khoản đã có trước migration này: admin và chủ shop coi như đã xác minh, tránh khóa họ.
UPDATE users SET email_verified_at = created_at
 WHERE email_verified_at IS NULL
   AND (role = 'admin' OR id IN (SELECT owner_user_id FROM shops));

CREATE TABLE IF NOT EXISTS email_tokens (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    purpose TEXT NOT NULL CHECK (purpose IN ('verify_email', 'reset_password')),
    token_hash CHAR(64) NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,
    used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_email_tokens_user_purpose ON email_tokens (user_id, purpose, created_at DESC);

CREATE TABLE IF NOT EXISTS seller_applications (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    shop_name VARCHAR(150) NOT NULL,
    province_code VARCHAR(4) NOT NULL REFERENCES provinces(code) ON DELETE RESTRICT,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    reject_reason VARCHAR(500),
    reviewed_by UUID REFERENCES users(id) ON DELETE SET NULL,
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_seller_applications_review CHECK (
        (status = 'pending' AND reviewed_at IS NULL)
        OR (status <> 'pending' AND reviewed_at IS NOT NULL)
    ),
    CONSTRAINT ck_seller_applications_reason CHECK (status = 'rejected' OR reject_reason IS NULL)
);
-- Mỗi người chỉ có một hồ sơ đang chờ duyệt.
CREATE UNIQUE INDEX IF NOT EXISTS uq_seller_applications_pending_user
    ON seller_applications (user_id) WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS ix_seller_applications_status_created
    ON seller_applications (status, created_at DESC, id DESC);

COMMIT;
