# Backend – môi trường phát triển

```bash
# từ thư mục e-commerce/
cp .env.example .env            # đổi POSTGRES_PORT/DATABASE_URL nếu cổng 5432 đã bị chiếm
docker compose up -d db         # Postgres 16; tự chạy apps/backend/migrations/*.sql lần đầu
python3 -m venv .venv && source .venv/bin/activate
pip install -r apps/backend/requirements.txt
set -a; source .env; set +a
pytest apps/backend/tests       # kiểm tra entity Orders/Payments/Reviews với DB thật
```

Reset DB (xóa dữ liệu, chạy lại migration): `docker compose down -v && docker compose up -d db`.

## Entity
- `src/orders/model.py`: Checkout, Order, OrderItem
- `src/orders/payments/model.py`: Payment, PaymentAllocation
- `src/reviews/model.py`: Review

Brand không có bảng riêng: là cột `products.brand` (VARCHAR(100), NULL được) dùng để lọc.
