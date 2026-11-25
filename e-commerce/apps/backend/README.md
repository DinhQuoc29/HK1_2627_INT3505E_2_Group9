# Backend – môi trường phát triển

Hướng dẫn chạy toàn bộ dự án (DB, backend, frontend) ở [README gốc](../../README.md). Tóm tắt phần backend:

```bash
# từ thư mục e-commerce/
cp .env.example .env            # điền JWT_SECRET_KEY; đổi POSTGRES_PORT/DATABASE_URL nếu cổng 5432 bị chiếm
docker compose up -d db         # Postgres 16; tự chạy apps/backend/migrations/*.sql lần đầu
cd apps/backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest -q   # test với DB thật (tự đọc ../../.env)
```

Reset DB (xóa dữ liệu, chạy lại migration): `docker compose down -v && docker compose up -d db`.

## Chạy backend (FastAPI)
```bash
# cần JWT_SECRET_KEY trong .env (>= 32 ký tự): python -c "import secrets; print(secrets.token_urlsafe(48))"
cd apps/backend/src && uvicorn app:create_app --factory --port 5000 --reload
```
- Swagger UI: http://localhost:5000/api/v1/docs · đặc tả: `apps/backend/openapi.yaml`
- Health check: `GET /healthz`
- Tài liệu API là `openapi.yaml` viết trước (design-first); trang `/docs` tự sinh của FastAPI được tắt để chỉ có một nguồn sự thật. `tests/test_openapi_contract.py` đảm bảo route trong code khớp spec.

## Bật đăng nhập Google / Facebook
- **Google:** Google Cloud Console → APIs & Services → Credentials → OAuth client ID (Web), Authorized JavaScript origins `http://localhost:5173`. Điền `GOOGLE_CLIENT_ID` (`.env` gốc) và `VITE_GOOGLE_CLIENT_ID` (`apps/web/.env`).
- **Facebook:** Meta for Developers → tạo app, thêm sản phẩm *Facebook Login* (Web), `http://localhost:5173` làm site URL/domain. Điền `FACEBOOK_APP_ID` và `FACEBOOK_APP_SECRET` (`.env` gốc, secret chỉ ở server) và `VITE_FACEBOOK_APP_ID` (`apps/web/.env`). App ở chế độ Development thì chỉ tài khoản có vai trò trong app mới đăng nhập được.
- Chưa cấu hình thì nút tương ứng bị mờ, backend trả 503 `…-unavailable`.
- **Kiểm tra cấu hình thật:** sau khi điền ID/secret, chạy `.venv/bin/python scripts/check_social_config.py`. Script báo ✔/✘ từng mục (định dạng ID, `.env` backend khớp `apps/web/.env`, Google tải được chứng chỉ, Facebook xác nhận cặp App ID/Secret) mà không in bí mật.
- **Lỗi thường gặp:** Google `origin_mismatch` → Authorized JavaScript origins phải đúng `http://localhost:5173` (không phải `127.0.0.1`); Facebook không mở được popup/báo thiếu quyền → app đang ở chế độ Development và tài khoản chưa được thêm vai trò, hoặc chưa thêm `http://localhost:5173/` vào "Miền được phép cho JavaScript SDK" (Facebook Login → Cài đặt, bật "Đăng nhập bằng JavaScript SDK"; không dùng App Domains vì Meta không nhận `localhost`); nút không phản ứng → chưa restart Vite sau khi sửa `apps/web/.env`.
- Migration `002_add_facebook_identity_provider.sql` cho phép provider `facebook`. DB đang chạy từ trước: `docker exec -i ecommerce-db psql -U ecommerce -d ecommerce < apps/backend/migrations/002_add_facebook_identity_provider.sql`.

## Tài khoản dev
`.venv/bin/python scripts/seed_dev_user.py` tạo một buyer mẫu trong DB local (thông tin đăng nhập nằm ở đầu file script; chạy lại vẫn an toàn, từ chối nếu DB không phải local).

## Auth API (`/api/v1`)
| Method | Path | Mô tả |
| --- | --- | --- |
| POST | `/users` | Đăng ký buyer (kèm mở phiên) |
| GET | `/users/me` | Hồ sơ người đang đăng nhập (kèm `providers`, `has_password`) |
| POST | `/users/me/identities` | Liên kết Google hoặc Facebook với người dùng đang đăng nhập |
| DELETE | `/users/me/identities/{provider}` | Hủy liên kết (không cho khi đó là cách đăng nhập duy nhất) |
| POST | `/auth/sessions` | Đăng nhập email/mật khẩu (sai 5 lần liên tiếp thì khóa 15 phút) |
| POST | `/auth/sessions/google` | Đăng nhập Google (ID token) |
| POST | `/auth/sessions/facebook` | Đăng nhập/đăng ký Facebook (access token; không tự gộp vào tài khoản trùng email) |
| POST | `/auth/tokens` | Đổi refresh token (cookie HttpOnly) lấy access token mới, có xoay vòng |
| DELETE | `/auth/sessions/current` | Đăng xuất, thu hồi phiên ngay |

Access token JWT 15 phút (claim `sid` trỏ `auth_sessions`, mỗi request kiểm tra phiên còn hiệu lực).
Lỗi trả `application/problem+json`. Mật khẩu băm bcrypt; refresh token chỉ lưu SHA-256.
Đăng ký/đăng nhập bị giới hạn `RATE_LIMIT_PER_MINUTE` request mỗi IP mỗi phút (429 + `Retry-After`; bộ nhớ trong tiến trình).

## Vai trò và phân quyền (buyer / seller / admin)
| Vai trò | Có được bằng cách | Quyền chính |
| --- | --- | --- |
| buyer | Đăng ký (`POST /users`) hoặc đăng nhập Google/Facebook lần đầu | Mua hàng, quản lý tài khoản |
| seller | Buyer đã xác minh email nộp hồ sơ (`POST /seller-applications`), **admin duyệt** thì thành seller và có shop | Quản lý shop (`GET /shops/me`) |
| admin | **Không tự đăng ký được.** Tạo bằng script bên dưới hoặc admin khác cấp | Quản trị người dùng (`/admin/users`) |

Vai trò đọc từ DB ở mỗi request nên đổi vai trò có hiệu lực ngay, không cần đăng nhập lại.

**Tạo admin đầu tiên** (idempotent; email đã có thì giữ mật khẩu và nâng lên admin):
```bash
cd e-commerce && set -a; source .env; set +a
ADMIN_EMAIL=admin@example.com ADMIN_PASSWORD='Admin12345' ADMIN_NAME='Quản trị' \
  .venv/bin/python apps/backend/scripts/create_admin.py
```
**Migration 003, 004** (`users.status`, `email_verified_at`, `email_tokens`, `seller_applications`): DB đã có sẵn thì chạy một lần
`docker exec -i ecommerce-db psql -U ecommerce < apps/backend/migrations/00X_....sql` (DB tạo mới tự chạy). Reset DB: `docker compose down -v && docker compose up -d db`.

| Method | Path | Vai trò | Mô tả |
| --- | --- | --- | --- |
| PUT | `/users/me/password` | đã đăng nhập | Đổi mật khẩu (hoặc đặt lần đầu cho tài khoản social); thu hồi các phiên khác |
| GET | `/admin/users` | admin | Danh sách, lọc `role`/`status`/`q`, phân trang cursor |
| GET | `/admin/users/{id}` | admin | Chi tiết |
| PATCH | `/admin/users/{id}` | admin | Khóa/mở khóa (`status`), cấp/thu quyền admin (`role`) |

Quy tắc: admin không tự sửa/khóa chính mình (409); seller đang có shop không đổi vai trò được, chỉ khóa được (409);
khóa tài khoản thu hồi mọi phiên ngay và chặn đăng nhập/làm mới token (403 `account-suspended`);
admin không nộp hồ sơ người bán được (403).

## Email, quên mật khẩu, duyệt người bán
**Email** chọn bằng `EMAIL_BACKEND` trong `.env`: `console` (mặc định, in nội dung + link ra log backend), `smtp`
(gửi thật; dev dùng Mailpit: `docker compose --profile mail up -d mailpit`, xem thư ở http://localhost:8025).
Link trong email trỏ về `APP_BASE_URL` (frontend). Gửi chạy nền nên không làm chậm API; lỗi SMTP chỉ ghi log.

| Method | Path | Mô tả |
| --- | --- | --- |
| POST | `/auth/email-verifications` | Gửi lại email xác minh (đã đăng nhập; cách nhau ≥ 60 giây) |
| POST | `/auth/email-verifications/confirmation` | Xác minh bằng `token` trong link (dùng một lần) |
| POST | `/auth/password-resets` | Yêu cầu đặt lại mật khẩu; **luôn 202** để không lộ email nào tồn tại |
| POST | `/auth/password-resets/confirmation` | Đặt mật khẩu mới bằng `token`; thu hồi mọi phiên |
| POST | `/seller-applications` | Buyer đã xác minh email nộp hồ sơ (`name`, `province_code`) và nhận email xác nhận |
| GET | `/seller-applications/me` | Hồ sơ gần nhất của tôi |
| GET | `/admin/seller-applications` | Admin: danh sách (`status`, cursor) |
| POST | `/admin/seller-applications/{id}/approval` | Admin duyệt: tạo shop + nâng seller + gửi email |
| POST | `/admin/seller-applications/{id}/rejection` | Admin từ chối kèm `reason` + gửi email; người nộp nộp lại được |

Token email: ngẫu nhiên 48 byte, DB chỉ lưu SHA-256, dùng một lần (đánh dấu nguyên tử), phát hành token mới thì link cũ
hết hiệu lực. Xác minh email có hiệu lực 24 giờ, đặt lại mật khẩu 60 phút. Đăng nhập Google tự coi email đã xác minh;
đặt lại mật khẩu thành công cũng chứng minh sở hữu email. Admin tạo bằng script cũng được coi là đã xác minh.

## Quản lý sản phẩm của người bán

Các API dưới `/api/v1/shops/me/products` dành cho người bán có gian hàng. `GET` hỗ trợ tìm theo tên, lọc trạng thái và phân trang. `POST` đăng sản phẩm, `PUT /{product_id}` sửa thông tin và tồn kho, còn `PATCH /{product_id}/status` ẩn hoặc hiện lại sản phẩm. `GET /api/v1/shops/me/product-categories` trả danh mục cấp 2 để chọn trong biểu mẫu.

Ảnh lưu dưới dạng URL HTTP hoặc HTTPS. Ảnh đầu danh sách làm ảnh đại diện. Tồn kho tính theo đơn vị nguyên, giá tính bằng VND.

Database khởi tạo mới tự nạp danh mục từ migration 005. Với container local đã chạy từ trước, nạp danh mục bằng lệnh dưới đây. Lệnh có thể chạy lại.

```powershell
docker compose exec -T db psql -X -v ON_ERROR_STOP=1 -U ecommerce -d ecommerce -f /docker-entrypoint-initdb.d/005_seed_product_categories.sql
```

## Entity
- `src/accounts/model.py`: User, UserIdentity, AuthSession, PrivacySettings
- `src/catalog/model.py`: Province, Shop, Category, Product, ProductImage
- `src/cart/model.py`: CartItem
- `src/orders/model.py`: Inventory, Checkout, Order, OrderItem
- `src/orders/payments/model.py`: Payment, PaymentAllocation
- `src/reviews/model.py`: Review

Brand không có bảng riêng: là cột `products.brand` (VARCHAR(100), NULL được) dùng để lọc.
