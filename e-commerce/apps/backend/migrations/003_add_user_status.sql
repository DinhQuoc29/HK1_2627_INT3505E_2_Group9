-- Trạng thái tài khoản: admin có thể tạm khóa (suspended) người dùng; khóa thì mọi phiên bị thu hồi.
-- Chạy được nhiều lần (idempotent). DB tạo mới chạy 001, 002, 003 theo thứ tự tên file.

BEGIN;

ALTER TABLE users ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'active';
ALTER TABLE users DROP CONSTRAINT IF EXISTS ck_users_status;
ALTER TABLE users ADD CONSTRAINT ck_users_status CHECK (status IN ('active', 'suspended'));
CREATE INDEX IF NOT EXISTS ix_users_created_at_id ON users (created_at DESC, id DESC);

COMMIT;
