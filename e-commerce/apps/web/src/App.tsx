import { GoogleOAuthProvider } from '@react-oauth/google'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import AccountPage from './buyer/AccountPage'
import SellerRegisterPage from './seller/SellerRegisterPage'
import SellerShopPage from './seller/SellerShopPage'
import { AuthProvider } from './shared/auth/AuthContext'
import AdminSellerApplicationsPage from './admin/AdminSellerApplicationsPage'
import AdminUsersPage from './admin/AdminUsersPage'
import ForgotPasswordPage from './shared/auth/pages/ForgotPasswordPage'
import ResetPasswordPage from './shared/auth/pages/ResetPasswordPage'
import VerifyEmailPage from './shared/auth/pages/VerifyEmailPage'
import { useAuth } from './shared/auth/AuthContext'
import { homeFor } from './shared/auth/roles'
import { GuestOnly, ProtectedRoute, RoleRoute } from './shared/auth/ProtectedRoute'
import LoginPage from './shared/auth/pages/LoginPage'
import RegisterPage from './shared/auth/pages/RegisterPage'

/** "/" và mọi đường dẫn lạ: về trang chủ theo vai trò (chưa đăng nhập thì ProtectedRoute đưa tới /login). */
function HomeRedirect() {
  const { user } = useAuth()
  return <Navigate to={user ? homeFor(user.role) : '/login'} replace />
}

/** Toàn bộ route + phiên đăng nhập (tách khỏi router để test bằng MemoryRouter). */
export function AppRoutes() {
  return (
        <AuthProvider>
          <Routes>
            <Route element={<GuestOnly />}>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
            </Route>
            {/* Link trong email: mở được cả khi đã hoặc chưa đăng nhập (có thể bấm từ thiết bị khác). */}
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />
            <Route path="/reset-password" element={<ResetPasswordPage />} />
            <Route path="/verify-email" element={<VerifyEmailPage />} />
            <Route element={<ProtectedRoute />}>
              <Route path="/account" element={<AccountPage />} />
              <Route element={<RoleRoute roles={['buyer', 'seller']} />}>
                <Route path="/seller/register" element={<SellerRegisterPage />} />
              </Route>
              <Route element={<RoleRoute roles={['seller']} redirectTo="/seller/register" />}>
                <Route path="/seller" element={<SellerShopPage />} />
              </Route>
              <Route element={<RoleRoute roles={['admin']} />}>
                <Route path="/admin" element={<AdminUsersPage />} />
                <Route path="/admin/sellers" element={<AdminSellerApplicationsPage />} />
              </Route>
              <Route path="*" element={<HomeRedirect />} />
            </Route>
          </Routes>
        </AuthProvider>
  )
}

export default function App() {
  return (
    <GoogleOAuthProvider clientId={import.meta.env.VITE_GOOGLE_CLIENT_ID ?? ''}>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </GoogleOAuthProvider>
  )
}
