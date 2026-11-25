import { Link, Navigate, Outlet, useLocation } from 'react-router-dom'
import type { Role } from '../api/client'
import { useAuth } from './AuthContext'
import { Spinner } from './components/ui'
import { homeFor, roleLabel } from './roles'

/** Chặn route cần đăng nhập; nhớ trang đang vào để quay lại sau khi đăng nhập. */
export function ProtectedRoute() {
  const { status } = useAuth()
  const location = useLocation()
  if (status === 'loading') return <div className="grid h-full place-items-center"><Spinner label="Đang tải…" /></div>
  if (status === 'anonymous') return <Navigate to="/login" replace state={{ from: location.pathname + location.search }} />
  return <Outlet />
}

/** Trang đăng nhập/đăng ký: đã đăng nhập thì chuyển tới trang chủ của vai trò. */
export function GuestOnly() {
  const { status, user } = useAuth()
  if (status === 'loading') return <div className="grid h-full place-items-center"><Spinner label="Đang tải…" /></div>
  if (status === 'authenticated' && user) return <Navigate to={homeFor(user.role)} replace />
  return <Outlet />
}

/** Giới hạn route theo vai trò (đặt BÊN TRONG ProtectedRoute). Sai vai trò: trang 403 hoặc chuyển hướng. */
export function RoleRoute({ roles, redirectTo }: { roles: Role[]; redirectTo?: string }) {
  const { user } = useAuth()
  if (!user) return null
  if (roles.includes(user.role)) return <Outlet />
  if (redirectTo) return <Navigate to={redirectTo} replace />
  return <Forbidden role={user.role} />
}

export function Forbidden({ role }: { role: Role }) {
  return (
    <div className="grid min-h-full place-items-center px-5">
      <div role="alert" className="max-w-sm text-center">
        <p className="text-5xl font-bold text-brand-600">403</p>
        <h1 className="mt-3 text-xl font-bold tracking-tight">Bạn không có quyền truy cập trang này</h1>
        <p className="mt-1.5 text-sm text-zinc-500">Tài khoản của bạn đang là {roleLabel[role].toLowerCase()}.</p>
        <Link to={homeFor(role)} className="mt-6 inline-block rounded-xl bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-brand-700">Về trang của tôi</Link>
      </div>
    </div>
  )
}
