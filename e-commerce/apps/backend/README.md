# Backend – môi trường phát triển

```bash
# từ thư mục e-commerce/
cp .env.example .env            # đổi POSTGRES_PORT/DATABASE_URL nếu cổng 5432 đã bị chiếm
docker compose up -d db         # Postgres 16; tự chạy apps/backend/migrations/*.sql lần đầu
python3 -m venv .venv && source .venv/bin/activate
pip install -r apps/backend/requirements.txt
set -a; source .env; set +a
pytest apps/backend/tests       # kiểm tra entity với DB thật
```

Reset DB (xóa dữ liệu, chạy lại migration): `docker compose down -v && docker compose up -d db`.

## Chạy backend (Flask)
```bash
# cần JWT_SECRET_KEY trong .env (>= 32 ký tự): python -c "import secrets; print(secrets.token_urlsafe(48))"
cd apps/backend/src && flask --app app run --port 5000
```
- Swagger UI: http://localhost:5000/api/v1/docs · đặc tả: `apps/backend/openapi.yaml`
- Health check: `GET /healthz`

## Auth API (`/api/v1`)
| Method | Path | Mô tả |
| --- | --- | --- |
| POST | `/users` | Đăng ký buyer (kèm mở phiên) |
| GET | `/users/me` | Hồ sơ người đang đăng nhập |
| POST | `/auth/sessions` | Đăng nhập email/mật khẩu (sai 5 lần liên tiếp thì khóa 15 phút) |
| POST | `/auth/sessions/google` | Đăng nhập Google (ID token) |
| POST | `/auth/tokens` | Đổi refresh token (cookie HttpOnly) lấy access token mới, có xoay vòng |
| DELETE | `/auth/sessions/current` | Đăng xuất, thu hồi phiên ngay |

Access token JWT 15 phút (claim `sid` trỏ `auth_sessions`, mỗi request kiểm tra phiên còn hiệu lực).
Lỗi trả `application/problem+json`. Mật khẩu băm bcrypt; refresh token chỉ lưu SHA-256.

## Entity
- `src/accounts/model.py`: User, UserIdentity, AuthSession, PrivacySettings
- `src/catalog/model.py`: Province, Shop, Category, Product, ProductImage
- `src/cart/model.py`: CartItem
- `src/orders/model.py`: Inventory, Checkout, Order, OrderItem
- `src/orders/payments/model.py`: Payment, PaymentAllocation
- `src/reviews/model.py`: Review

Brand không có bảng riêng: là cột `products.brand` (VARCHAR(100), NULL được) dùng để lọc.
