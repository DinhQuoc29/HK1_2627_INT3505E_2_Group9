# Tiến trình thực hiện

Cập nhật: 24/11/2026 · Nhánh: `feature/auth-login-register`

## 1. Đã hoàn thành

### Cơ sở dữ liệu
- `docs/Database_Tables.md`: data dictionary đủ 24 bảng. Bảng `brands` đã bỏ, thương hiệu là cột `products.brand`.
- `apps/backend/migrations/001_initial_commerce.sql`: tạo đủ 24 bảng, ràng buộc, index và seed 34 tỉnh/thành.
- `docker-compose.yml`: PostgreSQL 16, tự chạy migration ở lần khởi tạo đầu tiên. Biến môi trường mẫu ở `.env.example`.

### Entity (SQLAlchemy 2.x)
- Accounts: `User`, `UserIdentity`, `AuthSession`, `PrivacySettings`.
- Catalog: `Province`, `Shop`, `Category`, `Product`, `ProductImage`.
- Cart: `CartItem`.
- Order & Inventory: `Inventory`, `Checkout`, `Order`, `OrderItem`.
- Payment: `Payment`, `PaymentAllocation`.
- Reviews: `Review`.
- `tests/test_schema_sync.py` kiểm tra model khớp schema trong DB.

### Backend Auth (FastAPI)
- Endpoint dưới `/api/v1`:
  - `POST /users`: đăng ký.
  - `GET /users/me`: hồ sơ người dùng đang đăng nhập.
  - `POST /auth/sessions`: đăng nhập.
  - `POST /auth/sessions/google`: đăng nhập Google.
  - `POST /auth/sessions/facebook`: đăng nhập/đăng ký Facebook (xác minh token qua Graph API `debug_token`; không tự gộp vào tài khoản trùng email).
  - `POST /auth/tokens`: làm mới token.
  - `DELETE /auth/sessions/current`: đăng xuất.
  - `POST /users/me/identities`, `DELETE /users/me/identities/{provider}`: liên kết / hủy liên kết Google, Facebook khi đã đăng nhập (SPEC-01).
- Access token JWT 15 phút, claim `sid` trỏ tới `auth_sessions`; mỗi request kiểm tra phiên còn hiệu lực nên đăng xuất có hiệu lực ngay.
- Refresh token ngẫu nhiên, DB chỉ lưu SHA-256, nằm trong cookie HttpOnly và được xoay vòng.
- Mật khẩu băm bcrypt. Sai 5 lần liên tiếp thì khóa 15 phút (429 + `Retry-After`).
- Google: xác minh ID token, liên kết theo `(google, sub)` hoặc theo email đã xác minh; Google không phản hồi thì 503 và không tạo phiên hay tài khoản.
- Luồng đăng nhập thật được kiểm thử bằng token Google ký cục bộ (chữ ký, audience, issuer, hạn dùng) và Graph API giả cho Facebook; `scripts/check_social_config.py` kiểm tra cấu hình thật khi có ID/secret.
- Giới hạn tốc độ đăng ký/đăng nhập theo IP (429 + `Retry-After`).
- Lỗi thống nhất `application/problem+json`; cấu hình qua biến môi trường; log dạng JSON; `GET /healthz`.

### Frontend (React + TypeScript + Vite + Tailwind)
- Trang Đăng ký, Đăng nhập, trang tài khoản (xem, liên kết/hủy liên kết Google) và route guard.
- Tự làm mới access token khi hết hạn và gọi lại yêu cầu; phiên hết hạn hẳn thì về trang đăng nhập kèm thông báo. Giao diện sáng, tiếng Việt, tự chuyển tối theo hệ điều hành.
- Kiểm tra form bằng zod (khớp quy tắc backend), hiện lỗi 422/409/401/429/503 đúng chỗ, checklist mật khẩu theo thời gian thực.
- Access token chỉ giữ trong bộ nhớ; khôi phục phiên khi tải lại trang bằng cookie refresh.

### API contract
- `apps/backend/openapi.yaml`: 22 path, 24 operation, hợp lệ theo `openapi-spec-validator`.
  - Accounts: đã cài đặt.
  - Checkout, Payments, Orders, Inventory, Reviews: mới có đặc tả (design-first), chưa cài đặt.
- Swagger UI: `/api/v1/docs`.

## 2. Bằng chứng kiểm thử

| Phần | Kết quả |
| --- | --- |
| Backend (`pytest`, DB thật) | 61 test qua: đăng ký, đăng nhập, khóa tài khoản, refresh xoay vòng, đăng xuất, phân quyền, Google (giả lập), đồng bộ schema, hợp đồng OpenAPI |
| Frontend (`vitest`) | 39 test qua: schema form, thông báo lỗi, luồng đăng nhập/đăng ký, route guard, refresh chỉ gọi một lần |
| Typecheck và build | `tsc` và `vite build` sạch |
| Thử trên trình duyệt | Đăng ký → vào trang tài khoản → tải lại vẫn giữ phiên → đăng xuất thì phiên bị thu hồi trong DB |

## 3. Chưa làm

- Cài đặt backend cho Checkout, Orders, Payments, Inventory, Reviews (đã có entity và spec).
- Giao diện cho giỏ hàng, đơn hàng, đánh giá.
- Đăng nhập Google và Facebook chưa thử với nhà cung cấp thật (cần Client ID / Facebook App ID, xem mục 5).
- Quên mật khẩu, đổi mật khẩu, xác minh email: thiết kế DB hiện chưa có bảng cho các luồng này nên chưa làm.
- Mock server cho OpenAPI. Có thể chạy thủ công: `npx @stoplight/prism-cli mock apps/backend/openapi.yaml -p 4010`.
- Chưa có view hợp đồng đọc và phần lớn index tìm kiếm của `products`/`orders` trong migration.

## 4. Quyết định thiết kế và điểm còn mở

- Đăng ký chỉ tạo tài khoản buyer và đăng nhập luôn; seller và admin không tự đăng ký.
- Endpoint đặt theo danh từ số nhiều; chuyển trạng thái đơn mô hình hóa như tài nguyên con (`/orders/{id}/cancellation`).
- **Cần thống nhất:** SPEC-19 yêu cầu một lần đánh giá cho mỗi dòng hàng kể cả sau khi gỡ, nhưng `reviews.order_item_id` đang UNIQUE và chưa có cột đánh dấu đã gỡ. Đề xuất: gỡ review thì chuyển `status` sang `hidden`.
- Hai trường tính toán không có trong DB: `OrderItem.has_review` và `Review.author.full_name`.
- Mở nhiều tab và refresh cùng lúc có thể khiến một tab phải đăng nhập lại, vì refresh token được xoay vòng.

## 5. Cách chạy lại

- Backend, DB và migration: xem `apps/backend/README.md`.
- Frontend: xem `apps/web/README.md`.
- Bật đăng nhập Google/Facebook: xem mục "Bật đăng nhập Google / Facebook" trong `apps/backend/README.md`.
- Quyết định thiết kế đã đổi so với bản DB v1.1: `user_identities.provider` cho phép thêm `facebook` (migration 002); cần báo nhóm.

## 6. Kế hoạch tiếp theo

1. Cài đặt Checkout và Orders (Idempotency-Key, trừ kho, tách đơn theo shop, state machine) kèm test đồng thời.
2. Cài đặt Payment giả lập và hủy đơn hoàn kho/hoàn tiền.
3. Cài đặt Reviews (một review mỗi dòng hàng, tính lại điểm sản phẩm).
4. Thêm tag `orders`, `payments`, `inventory`, `reviews` vào `IMPLEMENTED_TAGS` trong `tests/test_openapi_contract.py` khi từng module xong.
5. Soạn Postman collection cho luồng checkout → thanh toán → hoàn tất → đánh giá.
