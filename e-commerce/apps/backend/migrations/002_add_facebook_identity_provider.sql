-- Cho phép đăng nhập Facebook: mở rộng CHECK của user_identities.provider.
-- Chạy được nhiều lần (idempotent). DB tạo mới chạy 001 rồi 002 theo thứ tự tên file.

BEGIN;

ALTER TABLE user_identities DROP CONSTRAINT IF EXISTS user_identities_provider_check;
ALTER TABLE user_identities DROP CONSTRAINT IF EXISTS ck_user_identities_provider;
ALTER TABLE user_identities
    ADD CONSTRAINT ck_user_identities_provider CHECK (provider IN ('google', 'facebook'));

COMMIT;
