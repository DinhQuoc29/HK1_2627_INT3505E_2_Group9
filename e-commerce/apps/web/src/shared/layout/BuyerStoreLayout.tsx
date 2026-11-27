import { useEffect, useRef, useState, type FormEvent, type ReactNode } from 'react'
import { Link, matchPath, useLocation, useNavigate } from 'react-router-dom'
import { useBuyerRequest } from '../../buyer/useBuyerRequest'
import { api, type User } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { homeFor, roleLabel } from '../auth/roles'
import { BRAND, Logo } from '../brand'
import { StoreIcon } from './StoreIcon'

const storeLinks = [
  { to: '/', label: 'Trang chủ' },
  { to: '/products', label: 'Sản phẩm' },
  { to: '/#danh-muc', label: 'Danh mục' },
] as const

const wrapper = 'mx-auto w-full max-w-7xl px-4 lg:px-8'
const textLink = 'rounded-sm py-2 transition-colors hover:text-(--store-primary)'
const accountItem = 'block w-full rounded-lg px-3 py-2 text-left text-sm hover:bg-(--store-soft) hover:text-(--store-primary)'

export function BuyerStoreLayout({ children, home = false }: { children: ReactNode; home?: boolean }) {
  const { status, user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [query, setQuery] = useState(() => new URLSearchParams(location.search).get('q') ?? '')

  useEffect(() => {
    setQuery(new URLSearchParams(location.search).get('q') ?? '')
  }, [location.pathname, location.search])

  useEffect(() => {
    if (location.hash) document.getElementById(location.hash.slice(1))?.scrollIntoView?.()
  }, [location.key, location.hash])

  function search(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const value = query.trim()
    const params = new URLSearchParams(matchPath('/products', location.pathname) ? location.search : '')
    params.delete('page')
    if (value) params.set('q', value)
    else params.delete('q')
    navigate(params.size ? `/products?${params}` : '/products')
  }

  return (
    <div className={`buyer-store flex min-h-full flex-col ${home ? 'store-home' : 'bg-zinc-50 dark:bg-zinc-950'}`}>
      <a href="#buyer-main" className="sr-only focus:not-sr-only focus:fixed focus:left-3 focus:top-3 focus:z-40 focus:rounded-lg focus:bg-white focus:px-4 focus:py-3 focus:text-(--store-primary)">
        Đến nội dung chính
      </a>
      <header className="store-chrome sticky top-0 z-30 border-b border-(--store-outline) bg-white/95 backdrop-blur-xl">
        <div className={`${wrapper} flex min-h-16 flex-wrap items-center gap-x-4 gap-y-0 pb-3 sm:gap-x-6 md:flex-nowrap md:pb-0`}>
          <Link to="/" aria-label={`${BRAND} - Trang chủ`} className="flex min-h-14 shrink-0 items-center rounded-sm">
            <Logo />
          </Link>
          <nav aria-label="Điều hướng mua sắm" className="hidden shrink-0 items-center gap-6 pl-4 font-semibold text-(--store-muted) lg:flex">
            {storeLinks.map(({ to, label }) => (
              <Link key={to} to={to} aria-current={location.pathname + location.hash === to ? 'page' : undefined} className={textLink}>{label}</Link>
            ))}
          </nav>

          <form onSubmit={search} role="search" className="order-last flex h-10 w-full min-w-0 items-stretch rounded-lg bg-(--store-soft) focus-within:ring-2 focus-within:ring-(--store-primary)/30 md:order-none md:max-w-xl md:flex-1">
            <label htmlFor="store-search" className="sr-only">Tìm sản phẩm</label>
            <button type="submit" aria-label="Tìm kiếm" className="grid w-10 shrink-0 cursor-pointer place-items-center rounded-l-lg text-(--store-muted) hover:text-(--store-primary)">
              <StoreIcon name="search" className="size-5" />
            </button>
            <input
              id="store-search"
              name="q"
              type="search"
              maxLength={255}
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Bạn đang tìm kiếm sản phẩm gì?"
              className="min-w-0 flex-1 pr-3 text-base placeholder:text-(--store-muted) focus:outline-none sm:text-sm"
            />
          </form>

          <div className="ml-auto flex shrink-0 items-center gap-2 sm:gap-3" aria-busy={status === 'loading'}>
            {home && user?.role === 'buyer' ? <CartWithCount key={user.id} /> : <CartLink />}
            {status === 'anonymous' && (
              <div className="hidden items-center gap-2 font-semibold text-(--store-muted) sm:flex">
                <Link to="/login" className={textLink}>Đăng nhập</Link>
                <span aria-hidden="true" className="text-[#8f706a]">/</span>
                <Link to="/register" className={textLink}>Đăng ký</Link>
              </div>
            )}
            {status !== 'loading' && <StoreAccount key={location.key} user={user} onLogout={async () => {
              await logout().catch(() => undefined)
              navigate('/login', { replace: true })
            }} />}
          </div>
        </div>
      </header>

      <main id="buyer-main" tabIndex={-1} className="min-w-0 flex-1 scroll-mt-32 md:scroll-mt-20">{children}</main>

      <footer className={`store-chrome border-t border-(--store-outline) bg-white py-10 ${home ? '' : 'mt-12'}`}>
        <div className={`${wrapper} flex flex-col items-center justify-between gap-4 md:flex-row`}>
          <Link to="/" aria-label={`${BRAND} - Trang chủ`} className="flex shrink-0 items-center rounded-sm"><Logo variant="compact" /></Link>
          <nav aria-label="Điều hướng chân trang" className="flex flex-wrap items-center justify-center gap-x-6 text-(--store-muted)">
            {storeLinks.map(({ to, label }) => <Link key={to} to={to} className={textLink}>{label}</Link>)}
            <Link to="/account" className={textLink}>Tài khoản</Link>
          </nav>
          <p className="text-center text-xs text-(--store-muted)">© {new Date().getFullYear()} {BRAND} Vietnam. Bảo lưu mọi quyền.</p>
        </div>
      </footer>
    </div>
  )
}

function CartWithCount() {
  const { state } = useBuyerRequest(api.cart)
  const count = state.status === 'ready'
    ? state.data.groups.reduce((total, { items }) => total + items.reduce((sum, item) => sum + item.quantity, 0), 0)
    : 0
  return <CartLink count={count} />
}

function CartLink({ count = 0 }: { count?: number }) {
  return (
    <Link to="/cart" aria-label={count ? `Giỏ hàng, ${count} sản phẩm` : 'Giỏ hàng'} className="relative grid size-10 place-items-center rounded-lg text-(--store-muted) transition-colors hover:bg-(--store-soft) hover:text-(--store-ink)">
      <StoreIcon name="cart" className="size-[22px]" />
      {count > 0 && <span aria-hidden="true" className="absolute top-0 right-0 grid h-[18px] min-w-[18px] place-items-center rounded-full bg-(--store-primary) px-1 text-[11px] font-semibold leading-none text-white">{count > 99 ? '99+' : count}</span>}
    </Link>
  )
}

function StoreAccount({ user, onLogout }: { user: User | null; onLogout: () => Promise<void> }) {
  const details = useRef<HTMLDetailsElement>(null)
  const summary = useRef<HTMLElement>(null)

  return (
    <details
      ref={details}
      className="relative"
      onBlur={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget)) event.currentTarget.open = false
      }}
      onKeyDown={(event) => {
        if (event.key === 'Escape' && event.currentTarget.open) {
          event.currentTarget.open = false
          summary.current?.focus()
        }
      }}
    >
      <summary ref={summary} aria-label="Tài khoản" className="store-account-trigger grid size-10 cursor-pointer list-none place-items-center rounded-full">
        <span className="grid size-8 place-items-center rounded-full bg-(--store-primary) text-white"><StoreIcon name="person" className="size-[18px]" /></span>
      </summary>
      <div className="absolute right-0 top-full mt-2 w-56 rounded-xl border border-(--store-outline) bg-white p-2 shadow-lg" onClick={() => { if (details.current) details.current.open = false }}>
        {user ? (
          <>
            <div className="mb-1 border-b border-(--store-outline) px-3 pt-2 pb-3">
              <p className="truncate font-semibold">{user.full_name}</p>
              <p className="text-xs text-(--store-muted)">{roleLabel[user.role]}</p>
            </div>
            <Link to="/account" className={accountItem}>Tài khoản</Link>
            {user.role === 'buyer' ? (
              <>
                <Link to="/orders" className={accountItem}>Đơn mua</Link>
                <Link to="/seller/register" className={accountItem}>Mở shop</Link>
              </>
            ) : <Link to={homeFor(user.role)} className={accountItem}>Khu vực của bạn</Link>}
            <button type="button" onClick={() => void onLogout()} className={`${accountItem} cursor-pointer`}>Đăng xuất</button>
          </>
        ) : (
          <>
            <Link to="/login" className={accountItem}>Đăng nhập</Link>
            <Link to="/register" className={accountItem}>Đăng ký</Link>
          </>
        )}
      </div>
    </details>
  )
}
