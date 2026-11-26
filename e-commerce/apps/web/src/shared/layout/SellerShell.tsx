import type { ReactNode } from 'react'
import { Link, matchPath, NavLink, useLocation } from 'react-router-dom'
import { SellerIcon, SellerInitials } from '../../seller/sellerUi'
import type { User } from '../api/client'
import { BRAND } from '../auth/components/AuthLayout'

const sellerNav = [
  { to: '/seller', label: 'Tổng quan', icon: 'overview', end: true },
  { to: '/seller/products', label: 'Sản phẩm', icon: 'products', end: true },
  { to: '/seller/orders', label: 'Đơn hàng', icon: 'orders', end: false },
  { to: '/account', label: 'Tài khoản', icon: 'account', end: true },
] as const

const focusRing = 'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-500'

export function SellerShell({ children, user, onLogout, verificationBanner }: {
  children: ReactNode
  user: User
  onLogout: () => void
  verificationBanner?: ReactNode
}) {
  const { pathname } = useLocation()
  const section = sellerNav.find(({ to, end }) => matchPath({ path: to, end }, pathname))
  const isOverview = section?.to === '/seller'
  const isManagement = section?.to === '/seller/products' || section?.to === '/seller/orders' || section?.to === '/account'
  const theme = isManagement ? 'seller-reference seller-management' : isOverview ? 'seller-reference seller-overview' : ''

  return (
    <div className={`seller-shell min-h-screen bg-(--seller-canvas) text-slate-900 lg:grid lg:grid-cols-[230px_minmax(0,1fr)] lg:grid-rows-[auto_1fr] dark:bg-slate-950 dark:text-slate-100 ${theme}`}>
      <a href="#seller-main" className="sr-only focus:not-sr-only focus:absolute focus:left-3 focus:top-3 focus:z-40 focus:rounded-lg focus:bg-white focus:px-4 focus:py-3 focus:text-brand-700">
        Đến nội dung chính
      </a>

      <header className="seller-reference z-20 flex min-h-14 min-w-0 items-center justify-between gap-3 border-b border-slate-200/80 bg-white/95 px-4 text-slate-900 backdrop-blur-sm sm:px-6 lg:sticky lg:top-0 lg:col-start-2 lg:row-start-1">
        <div className="flex min-w-0 items-center gap-1.5 text-[13px] text-slate-500">
          <Link to="/seller" className={`flex min-w-0 items-center gap-2 rounded py-2 font-medium hover:text-slate-700 ${focusRing}`}>
            <span className="grid size-7 shrink-0 place-items-center rounded-lg bg-(--seller-accent) text-white lg:hidden">
              <SellerIcon name="bag" className="size-4" />
            </span>
            Kênh người bán
          </Link>
          {section && (
            <span className="hidden items-center gap-1.5 font-semibold text-slate-800 lg:flex">
              <SellerIcon name="chevron" className="size-3.5 text-slate-400" />
              {section.label}
            </span>
          )}
        </div>

        <div className="flex min-w-0 items-center gap-2 sm:gap-4">
          <div className="hidden min-w-0 items-center gap-2 sm:flex">
            <span aria-hidden="true" className="grid size-8 shrink-0 place-items-center rounded-full bg-(--seller-accent) text-xs font-bold text-white">
              <SellerInitials name={user.full_name} />
            </span>
            <span className="min-w-0">
              <span title={user.full_name} className="block max-w-48 truncate text-[13px] font-semibold leading-tight text-slate-800">{user.full_name}</span>
              <span className="block text-[11px] text-slate-400">Người bán</span>
            </span>
          </div>
          <button
            type="button"
            onClick={onLogout}
            className={`inline-flex min-h-11 shrink-0 items-center gap-1.5 rounded-lg px-2 text-xs font-semibold text-slate-600 transition hover:bg-slate-100 hover:text-slate-900 ${focusRing}`}
          >
            <SellerIcon name="logout" className="size-4 text-slate-400" />
            Đăng xuất
          </button>
        </div>
      </header>

      <aside className="seller-reference min-w-0 border-b border-slate-200/80 bg-white text-slate-900 lg:sticky lg:top-0 lg:col-start-1 lg:row-span-2 lg:row-start-1 lg:flex lg:h-dvh lg:flex-col lg:self-start lg:overflow-y-auto lg:border-r lg:border-b-0">
        <Link to="/seller" className={`hidden min-h-14 shrink-0 items-center gap-2.5 border-b border-slate-100 px-4 lg:flex ${focusRing} focus-visible:-outline-offset-2`}>
          <span className="grid size-8 shrink-0 place-items-center rounded-lg bg-(--seller-accent) text-white shadow-sm">
            <SellerIcon name="bag" />
          </span>
          <span className="min-w-0">
            <span className="block text-sm font-bold leading-tight text-slate-800">{BRAND}</span>
            <span className="block text-[11px] text-slate-400">Kênh người bán</span>
          </span>
        </Link>
        <nav aria-label="Điều hướng kênh người bán" className="grid grid-cols-2 gap-1 p-2 min-[360px]:grid-cols-4 sm:px-6 lg:grid-cols-1 lg:px-2 lg:py-3">
          {sellerNav.map(({ to, label, icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) => [
                'flex min-h-12 min-w-0 flex-col items-center justify-center gap-1 rounded-md border-b-2 px-1.5 text-xs font-medium transition sm:flex-row sm:gap-1.5 lg:min-h-10 lg:justify-start lg:gap-2.5 lg:border-b-0 lg:border-l-2 lg:px-3 lg:text-[13px]',
                focusRing,
                isActive
                  ? 'border-(--seller-accent) bg-(--seller-nav-active) text-(--seller-accent)'
                  : 'border-transparent text-slate-600 hover:bg-slate-50 hover:text-slate-900 [&>svg]:text-slate-400',
              ].join(' ')}
            >
              <SellerIcon name={icon} className="size-4 lg:size-[18px]" />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>
        {user.email_verified && (
          <div className="mt-auto hidden border-t border-slate-100 p-3 lg:block">
            <div className="flex items-center gap-2 rounded-lg border border-slate-100 bg-slate-50 px-2.5 py-2.5 text-xs font-medium text-slate-700">
              <SellerIcon name="verified" className="size-4 text-emerald-600" />
              Email đã xác minh
            </div>
          </div>
        )}
      </aside>

      <div className="min-w-0 lg:col-start-2 lg:row-start-2">
        {verificationBanner}
        <main id="seller-main" tabIndex={-1} className={`mx-auto min-w-0 space-y-5 px-4 py-5 sm:px-6 sm:py-6 lg:scroll-mt-16 ${isManagement ? 'max-w-7xl lg:px-8 lg:py-8' : 'max-w-6xl'}`}>
          {children}
        </main>
      </div>
    </div>
  )
}
