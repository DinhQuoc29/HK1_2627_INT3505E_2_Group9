import { useState, type ReactNode } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { Alert } from '../auth/components/ui'
import { describeError } from '../auth/errors'
import { Logo } from '../auth/components/AuthLayout'
import { homeFor, roleLabel } from '../auth/roles'
import { BuyerStoreLayout } from './BuyerStoreLayout'

const adminNav = [{ to: '/admin', label: 'Người dùng' }, { to: '/admin/sellers', label: 'Duyệt người bán' }, { to: '/account', label: 'Tài khoản' }] as const

const sellerNav = [
  { to: '/seller', label: 'Tổng quan' },
  { to: '/seller/products', label: 'Sản phẩm' },
  { to: '/seller/orders', label: 'Đơn hàng' },
  { to: '/account', label: 'Tài khoản' },
] as const

function SellerNavigation() {
  return (
    <nav
      aria-label="Điều hướng kênh người bán"
      className="grid grid-cols-2 gap-1 self-start rounded-2xl border border-zinc-200 bg-white p-2 text-sm font-medium sm:grid-cols-4 lg:grid-cols-1 dark:border-zinc-800 dark:bg-zinc-900"
    >
      {sellerNav.map(({ to, label }) => (
        <NavLink
          key={to}
          to={to}
          end={to !== '/seller/orders'}
          className={({ isActive }) => [
            'flex min-h-11 flex-1 items-center justify-center whitespace-nowrap rounded-xl px-2 py-2 transition sm:px-4 lg:justify-start',
            'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-500',
            isActive
              ? 'bg-brand-50 font-semibold text-brand-700 dark:bg-brand-900/35 dark:text-brand-100'
              : 'text-zinc-600 hover:bg-zinc-100 dark:text-zinc-300 dark:hover:bg-zinc-800',
          ].join(' ')}
        >
          {label}
        </NavLink>
      ))}
    </nav>
  )
}

/** Nhắc xác minh email (cần để đăng ký bán hàng) kèm nút gửi lại. */
function VerifyEmailBanner() {
  const [state, setState] = useState<{ tone: 'success' | 'error'; text: string }>()
  const [busy, setBusy] = useState(false)
  const resend = async () => {
    setBusy(true)
    try {
      await api.resendVerification()
      setState({ tone: 'success', text: 'Đã gửi email xác minh. Hãy kiểm tra hộp thư của bạn.' })
    } catch (e) { setState({ tone: 'error', text: describeError(e).message ?? 'Chưa gửi được email.' }) } finally { setBusy(false) }
  }
  return (
    <div className="border-b border-amber-200 bg-amber-50 text-sm text-amber-900 dark:border-amber-900/60 dark:bg-amber-950/40 dark:text-amber-200">
      <div className="mx-auto flex max-w-5xl flex-wrap items-center gap-x-4 gap-y-2 px-5 py-2.5">
        {state ? <Alert tone={state.tone}>{state.text}</Alert> : <span>Email của bạn chưa được xác minh.</span>}
        {state?.tone !== 'success' && (
          <button type="button" onClick={resend} disabled={busy} className="font-semibold underline underline-offset-2 disabled:opacity-60">Gửi lại email xác minh</button>
        )}
      </div>
    </div>
  )
}

/** Khung trang sau đăng nhập: logo, menu theo vai trò, tên người dùng và nút đăng xuất. */
export function AppShell({ children, width = 'max-w-3xl' }: { children: ReactNode; width?: string }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  if (!user) return null
  const { role } = user
  if (role === 'buyer') {
    return (
      <BuyerStoreLayout>
        {!user.email_verified && <VerifyEmailBanner />}
        <div className={`mx-auto min-w-0 space-y-6 px-4 py-7 sm:px-6 sm:py-10 ${width}`}>{children}</div>
      </BuyerStoreLayout>
    )
  }
  const containerWidth = role === 'seller' ? 'max-w-6xl' : width
  return (
    <div className="min-h-full bg-zinc-50 dark:bg-zinc-950">
      <header className="border-b border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900">
        <div className={`mx-auto flex min-h-16 flex-wrap items-center justify-between gap-3 px-5 py-2 ${containerWidth}`}>
          <div className="flex items-center gap-6">
            <Link to={homeFor(role)} aria-label="Trang chủ"><Logo /></Link>
            {role === 'seller' ? (
              <span className="hidden border-l border-zinc-200 pl-6 text-sm font-semibold text-zinc-600 sm:block dark:border-zinc-700 dark:text-zinc-300">
                Kênh người bán
              </span>
            ) : (
              <nav aria-label="Điều hướng chính" className="flex gap-1 text-sm font-medium">
                {adminNav.map((n) => (
                  <NavLink key={n.to} to={n.to} end className={({ isActive }) => `rounded-lg px-3 py-1.5 transition hover:bg-zinc-100 dark:hover:bg-zinc-800 ${isActive ? 'bg-brand-50 text-brand-700 dark:bg-zinc-800' : 'text-zinc-600 dark:text-zinc-300'}`}>{n.label}</NavLink>
                ))}
              </nav>
            )}
          </div>
          <div className="flex items-center gap-3 text-sm">
            <span className="hidden text-right sm:block">
              <span className="block font-medium leading-tight">{user.full_name}</span>
              <span className="text-xs text-zinc-500">{roleLabel[user.role]}</span>
            </span>
            <button
              type="button"
              onClick={async () => { await logout(); navigate('/login', { replace: true }) }}
              className="rounded-xl border border-zinc-300 px-3.5 py-2 font-medium transition hover:bg-zinc-50 dark:border-zinc-700 dark:hover:bg-zinc-800"
            >
              Đăng xuất
            </button>
          </div>
        </div>
      </header>
      {!user.email_verified && <VerifyEmailBanner />}
      {role === 'seller' ? (
        <div className={`mx-auto grid gap-6 px-5 py-6 lg:grid-cols-[13rem_minmax(0,1fr)] lg:py-10 ${containerWidth}`}>
          <SellerNavigation />
          <main className="min-w-0 space-y-6">{children}</main>
        </div>
      ) : (
        <main className={`mx-auto space-y-6 px-5 py-10 ${containerWidth}`}>{children}</main>
      )}
    </div>
  )
}
