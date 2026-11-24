# Web (React + TypeScript + Vite + Tailwind)

```bash
cd apps/web
npm install
cp .env.example .env     # điền VITE_GOOGLE_CLIENT_ID để bật đăng nhập Google
npm run dev              # http://localhost:5173 (proxy /api -> http://localhost:5000)
npm test                 # vitest
npm run build
```

Cần chạy backend (xem `apps/backend/README.md`). Google: tạo OAuth Client ID (Web) trên Google Cloud Console,
thêm `http://localhost:5173` vào *Authorized JavaScript origins*.

## Cấu trúc
- `src/shared/api/client.ts`: gọi API, đọc lỗi problem+json; access token chỉ nằm trong bộ nhớ, refresh qua cookie HttpOnly
- `src/shared/auth/`: AuthContext, route guard, trang Đăng nhập/Đăng ký, schema kiểm tra form (khớp backend)
- `src/buyer/AccountPage.tsx`: trang sau đăng nhập
