import { GoogleOAuthProvider } from '@react-oauth/google'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import AccountPage from './buyer/AccountPage'
import BuyerHomePage from './buyer/BuyerHomePage'
import { BuyerWorkflowPage } from './buyer/BuyerWorkflowPage'
import CatalogProductsPage from './buyer/catalog/CatalogProductsPage'
import CatalogProductDetailPage from './buyer/catalog/CatalogProductDetailPage'
import BuyerCartPage from './buyer/commerce/BuyerCartPage'
import SellerRegisterPage from './seller/SellerRegisterPage'
import SellerShopPage from './seller/SellerShopPage'
import SellerProductsPage from './seller/products/SellerProductsPage'
import SellerOrdersPage from './seller/orders/SellerOrdersPage'
import SellerOrderDetailPage from './seller/orders/SellerOrderDetailPage'
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
import { Spinner } from './shared/auth/components/ui'

/** Đưa từng vai trò về khu vực phù hợp nếu truy cập trực tiếp trang mua sắm. */
function HomeRedirect() {
  const { user } = useAuth()
  return <Navigate to={user ? homeFor(user.role) : '/login'} replace />
}

/** Trang chủ cửa hàng mở công khai; seller/admin quay về khu vực làm việc của họ. */
function StoreHomeRoute() {
  const { status, user } = useAuth()
  if (status === 'loading') return <div className="grid h-full place-items-center"><Spinner label="Đang tải…" /></div>
  if (user && user.role !== 'buyer') return <Navigate to={homeFor(user.role)} replace />
  return <BuyerHomePage />
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
            <Route path="/" element={<StoreHomeRoute />} />
            <Route path="/products" element={<CatalogProductsPage />} />
            <Route path="/products/:productId" element={<CatalogProductDetailPage />} />
            <Route element={<ProtectedRoute />}>
              <Route path="/account" element={<AccountPage />} />
              <Route element={<RoleRoute roles={['buyer']} redirectTo="/account" />}>
                <Route path="/cart" element={<BuyerCartPage />} />
                <Route path="/checkout" element={<BuyerWorkflowPage
                  title="Thanh toán"
                  description="Xác nhận thông tin mua hàng sau khi hệ thống kiểm tra lại giá và số lượng còn trong kho."
                  icon="✓"
                  nextStep="Luồng xác nhận thanh toán và kết quả giao dịch sẽ được kết nối ở bước checkout."
                  actionHref="/cart"
                  actionLabel="Quay lại giỏ hàng"
                />} />
                <Route path="/orders" element={<BuyerWorkflowPage
                  title="Đơn mua"
                  description="Theo dõi các đơn theo từng shop và xem trạng thái giao hàng mới nhất."
                  icon="▤"
                  nextStep="Lịch sử mua hàng, chi tiết đơn và thao tác hủy đủ điều kiện sẽ được kết nối ở bước đơn hàng."
                  actionHref="/products"
                  actionLabel="Mua sắm tiếp"
                />} />
                <Route path="/orders/:orderId" element={<BuyerWorkflowPage
                  title="Chi tiết đơn hàng"
                  description="Xem sản phẩm, số lượng, giá đã mua và tiến trình giao của shop."
                  icon="↗"
                  nextStep="Thông tin đơn hàng và các mốc giao nhận sẽ được kết nối ở bước lịch sử đơn."
                  actionHref="/orders"
                  actionLabel="Quay lại đơn mua"
                />} />
              </Route>
              <Route element={<RoleRoute roles={['buyer', 'seller']} />}>
                <Route path="/seller/register" element={<SellerRegisterPage />} />
                <Route element={<RoleRoute roles={['seller']} redirectTo="/seller/register" />}>
                  <Route path="/seller" element={<SellerShopPage />} />
                  <Route path="/seller/products" element={<SellerProductsPage />} />
                  <Route path="/seller/orders" element={<SellerOrdersPage />} />
                  <Route path="/seller/orders/:orderId" element={<SellerOrderDetailPage />} />
                </Route>
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
