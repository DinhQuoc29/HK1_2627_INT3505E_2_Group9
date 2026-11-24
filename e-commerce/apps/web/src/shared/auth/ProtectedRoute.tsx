import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from './AuthContext'
import { Spinner } from './components/ui'

/** Chặn route cần đăng nhập; nhớ trang đang vào để quay lại sau khi đăng nhập. */
export function ProtectedRoute() {
  const { status } = useAuth()
  const location = useLocation()
  if (status === 'loading') return <div className="grid h-full place-items-center"><Spinner label="Đang tải…" /></div>
  if (status === 'anonymous') return <Navigate to="/login" replace state={{ from: location.pathname + location.search }} />
  return <Outlet />
}

/** Trang đăng nhập/đăng ký: đã đăng nhập thì chuyển đi chỗ khác. */
export function GuestOnly() {
  const { status } = useAuth()
  if (status === 'loading') return <div className="grid h-full place-items-center"><Spinner label="Đang tải…" /></div>
  if (status === 'authenticated') return <Navigate to="/account" replace />
  return <Outlet />
}
