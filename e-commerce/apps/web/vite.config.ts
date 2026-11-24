import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// Dev: proxy /api sang backend để trình duyệt coi là cùng origin (cookie refresh HttpOnly, không cần CORS).
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: { '/api': { target: 'http://localhost:5000', changeOrigin: false } },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
    css: false,
    // Test độc lập với apps/web/.env của từng máy (mặc định: chưa cấu hình nhà cung cấp nào).
    env: { VITE_GOOGLE_CLIENT_ID: '', VITE_FACEBOOK_APP_ID: '' },
  },
})
