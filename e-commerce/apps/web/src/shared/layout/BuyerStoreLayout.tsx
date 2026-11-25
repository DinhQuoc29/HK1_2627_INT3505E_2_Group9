import { useEffect, useState, type FormEvent, type ReactNode } from 'react'
import { Link, matchPath, NavLink, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { Logo } from '../auth/components/AuthLayout'
import { homeFor, roleLabel } from '../auth/roles'

const buyerLinks = [
  { to: '/', label: 'Trang chủ', end: true },
  { to: '/products', label: 'Sản phẩm', end: false },
  { to: '/cart', label: 'Giỏ hàng', end: true, buyerOnly: true },
  { to: '/orders', label: 'Đơn mua', end: false, buyerOnly: true },
  { to: '/account', label: 'Tài khoản', end: true, signedInOnly: true },
] as const

export function BuyerStoreLayout({ children }: { children: ReactNode }) {
  const { status, user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [query, setQuery] = useState('')

  useEffect(() => {
    setQuery(new URLSearchParams(location.search).get('q') ?? '')
  }, [location.pathname, location.search])

  const search = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const value = query.trim()
    const params = new URLSearchParams(matchPath('/products', location.pathname) ? location.search : '')
    params.delete('page')
    if (value) params.set('q', value)
    else params.delete('q')
    navigate(params.size ? `/products?${params}` : '/products')
  }

  const visibleLinks = buyerLinks.filter((item) => {
    if ('buyerOnly' in item && item.buyerOnly && user?.role !== 'buyer') return false
    if ('signedInOnly' in item && item.signedInOnly && !user) return false
    return true
  })

  return (
    <div className="flex min-h-full flex-col bg-zinc-50 dark:bg-zinc-950">
      <a href="#buyer-main" className="sr-only focus:not-sr-only focus:absolute focus:left-3 focus:top-3 focus:z-30 focus:rounded-xl focus:bg-white focus:px-4 focus:py-3 focus:text-brand-700">
        Đến nội dung chính
      </a>
      <header className="z-20 border-b border-zinc-200 bg-white/95 backdrop-blur md:sticky md:top-0 dark:border-zinc-800 dark:bg-zinc-900/95">
        <div className="mx-auto max-w-7xl px-3 sm:px-6">
          <div className="flex min-h-[4.5rem] flex-wrap items-center gap-2 py-3 sm:gap-3">
            <Link to="/" aria-label="E-Market - Trang chủ" className="shrink-0">
              <Logo />
            </Link>

            <form onSubmit={search} role="search" className="order-3 flex w-full min-w-0 md:order-none md:ml-4 md:flex-1">
              <label htmlFor="store-search" className="sr-only">Tìm sản phẩm</label>
              <div className="flex w-full overflow-hidden rounded-xl border border-zinc-200 bg-zinc-50 focus-within:border-brand-500 focus-within:ring-2 focus-within:ring-brand-100 dark:border-zinc-700 dark:bg-zinc-950 dark:focus-within:ring-brand-900">
                <input
                  id="store-search"
                  name="q"
                  type="search"
                  maxLength={255}
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="Tìm sản phẩm bạn cần"
                  className="min-h-11 min-w-0 flex-1 bg-transparent px-4 text-sm outline-none placeholder:text-zinc-400"
                />
                <button type="submit" aria-label="Tìm kiếm" className="grid min-h-11 w-12 shrink-0 place-items-center bg-brand-600 text-white transition hover:bg-brand-700 focus-visible:-outline-offset-2 focus-visible:outline-2 focus-visible:outline-white">
                  <svg viewBox="0 0 24 24" className="size-5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden>
                    <circle cx="10.8" cy="10.8" r="6.8" /><path d="m16 16 4.5 4.5" />
                  </svg>
                </button>
              </div>
            </form>

            <div className="ml-auto flex shrink-0 items-center gap-1 text-sm sm:gap-2" aria-busy={status === 'loading'}>
              {status === 'loading' ? <div aria-hidden className="h-11 w-24" /> : user ? (
                <>
                  <Link to={user.role === 'buyer' ? '/account' : homeFor(user.role)} className="hidden max-w-36 truncate rounded-lg px-2 py-2 text-right hover:bg-zinc-100 sm:block dark:hover:bg-zinc-800">
                    <span className="block max-w-36 truncate font-semibold">{user.full_name}</span>
                    <span className="block text-xs text-zinc-500">{roleLabel[user.role]}</span>
                  </Link>
                  <button
                    type="button"
                    onClick={async () => { await logout(); navigate('/login', { replace: true }) }}
                    className="min-h-11 rounded-xl border border-zinc-300 px-3 font-medium transition hover:bg-zinc-50 dark:border-zinc-700 dark:hover:bg-zinc-800"
                  >
                    Đăng xuất
                  </button>
                </>
              ) : (
                <>
                  <Link to="/login" className="inline-flex min-h-11 items-center rounded-xl px-2 font-semibold text-zinc-700 transition hover:bg-zinc-100 sm:px-3 dark:text-zinc-200 dark:hover:bg-zinc-800">Đăng nhập</Link>
                  <Link to="/register" className="inline-flex min-h-11 items-center rounded-xl bg-brand-600 px-2 font-semibold text-white transition hover:bg-brand-700 sm:px-3">Đăng ký</Link>
                </>
              )}
            </div>
          </div>

          <nav aria-label="Điều hướng mua sắm" className="flex flex-wrap gap-x-1 pb-2 text-sm font-medium">
            {visibleLinks.map(({ to, label, end }) => (
              <NavLink
                key={to}
                to={to}
                end={end}
                className={({ isActive }) => [
                  'flex min-h-11 shrink-0 items-center rounded-lg px-2 transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-500 sm:px-3',
                  isActive
                    ? 'bg-brand-50 text-brand-700 dark:bg-brand-900/35 dark:text-brand-100'
                    : 'text-zinc-600 hover:bg-zinc-100 dark:text-zinc-300 dark:hover:bg-zinc-800',
                ].join(' ')}
              >
                {label}
              </NavLink>
            ))}
            {user?.role === 'buyer' && (
              <Link to="/seller/register" className="flex min-h-11 shrink-0 items-center rounded-lg px-2 text-zinc-500 transition hover:bg-zinc-100 hover:text-zinc-800 sm:ml-auto sm:px-3 dark:hover:bg-zinc-800 dark:hover:text-zinc-100">
                Mở shop
              </Link>
            )}
          </nav>
        </div>
      </header>
      <main id="buyer-main" tabIndex={-1} className="min-w-0 flex-1 md:scroll-mt-36">{children}</main>
      <footer className="mt-12 border-t border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-6 text-xs text-zinc-500 sm:px-6">
          <span>© {new Date().getFullYear()} E-Market</span>
          <span>Mua sắm thuận tiện từ nhiều shop</span>
        </div>
      </footer>
    </div>
  )
}
