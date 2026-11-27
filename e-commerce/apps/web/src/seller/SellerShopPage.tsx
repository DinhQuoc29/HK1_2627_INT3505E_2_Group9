import { useEffect, useState } from 'react'
import { ApiError, api, type Shop } from '../shared/api/client'
import { useAuth } from '../shared/auth/AuthContext'
import { AppShell } from '../shared/layout/AppShell'
import { Alert, Button, Spinner } from '../shared/auth/components/ui'
import { describeError } from '../shared/auth/errors'
import { SellerIcon, SellerInitials, sellerCard } from './sellerUi'
import { ShopEditor } from './shop/ShopEditor'
import { ShopStatsPanel } from './shop/ShopStatsPanel'

type ShopState =
  | { status: 'loading' }
  | { status: 'ready'; shop: Shop }
  | { status: 'error'; message: string; canRetry: boolean }

const shopDate = new Intl.DateTimeFormat('vi-VN', { dateStyle: 'medium', timeZone: 'Asia/Ho_Chi_Minh' })
const updateTime = new Intl.DateTimeFormat('vi-VN', { timeStyle: 'short', timeZone: 'Asia/Ho_Chi_Minh' })

function ShopOverview({ onStatsLoaded }: { onStatsLoaded: (updatedAt: Date) => void }) {
  const [state, setState] = useState<ShopState>({ status: 'loading' })
  const [attempt, setAttempt] = useState(0)
  const [editing, setEditing] = useState(false)
  const [notice, setNotice] = useState<string>()

  useEffect(() => {
    let cancelled = false
    api.myShop().then(
      (shop) => {
        if (!cancelled) setState({ status: 'ready', shop })
      },
      (error: unknown) => {
        if (cancelled) return

        if (error instanceof ApiError && error.status === 404 && error.slug === 'shop-not-found') {
          setState({
            status: 'error',
            message: 'Tài khoản này chưa có shop liên kết. Vui lòng liên hệ quản trị viên.',
            canRetry: false,
          })
          return
        }

        setState({
          status: 'error',
          message: describeError(error).message ?? 'Không tải được thông tin shop.',
          canRetry: error instanceof ApiError && (error.status === 0 || error.status >= 500),
        })
      },
    )
    return () => { cancelled = true }
  }, [attempt])

  if (state.status === 'loading') return <section className={sellerCard}><Spinner label="Đang tải shop…" /></section>

  if (state.status === 'error') {
    const retry = () => {
      setState({ status: 'loading' })
      setAttempt((previous) => previous + 1)
    }
    return (
      <section className={`${sellerCard} space-y-4`}>
        <Alert>{state.message}</Alert>
        {state.canRetry && (
          <div className="w-fit">
            <Button type="button" onClick={retry}>Thử lại</Button>
          </div>
        )}
      </section>
    )
  }

  const { shop } = state
  return (
    <>
      {notice && <Alert tone="success">{notice}</Alert>}
      <section aria-label="Thông tin shop" className={sellerCard}>
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex min-w-0 items-start gap-3.5 sm:items-center">
            <span aria-hidden="true" className="grid size-13 shrink-0 place-items-center rounded-lg bg-[linear-gradient(135deg,var(--seller-accent),var(--seller-avatar-end))] text-lg font-bold text-white shadow-sm">
              <SellerInitials name={shop.name} />
            </span>
            <div className="min-w-0">
              <h2 className="text-base font-bold leading-tight wrap-anywhere">{shop.name}</h2>
              <dl className="mt-1.5 grid grid-cols-[auto_minmax(0,1fr)] gap-x-2 gap-y-1.5 text-[13px] leading-5 text-slate-500 sm:flex sm:flex-wrap sm:gap-x-5 dark:text-slate-400">
                <div className="col-span-2 grid min-w-0 grid-cols-subgrid items-start sm:flex sm:gap-1.5">
                  <dt className="flex shrink-0 items-center gap-1.5 whitespace-nowrap">
                    <SellerIcon name="location" className="size-4 text-slate-400" />
                    Nơi bán:
                  </dt>
                  <dd className="min-w-0 font-medium text-slate-700 wrap-anywhere dark:text-slate-200">{shop.province.name}</dd>
                </div>
                <div className="col-span-2 grid min-w-0 grid-cols-subgrid items-start sm:flex sm:gap-1.5">
                  <dt className="flex shrink-0 items-center gap-1.5 whitespace-nowrap">
                    <SellerIcon name="calendar" className="size-4 text-slate-400" />
                    Mở shop từ:
                  </dt>
                  <dd className="min-w-0 font-medium text-slate-700 dark:text-slate-200">
                    <time dateTime={shop.created_at}>{shopDate.format(new Date(shop.created_at))}</time>
                  </dd>
                </div>
              </dl>
            </div>
          </div>
          {!editing && (
            <button
              type="button"
              className="inline-flex min-h-11 shrink-0 items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 text-[13px] font-medium text-slate-700 shadow-xs transition hover:bg-slate-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-(--seller-accent) dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
              onClick={() => { setNotice(undefined); setEditing(true) }}
            >
              <SellerIcon name="edit" className="size-4 text-slate-500" />
              Chỉnh sửa thông tin
            </button>
          )}
        </div>
        {editing && (
          <ShopEditor
            shop={shop}
            onSaved={(updated) => {
              setState({ status: 'ready', shop: updated })
              setEditing(false)
              setNotice('Đã lưu thông tin gian hàng.')
            }}
            onCancel={() => setEditing(false)}
          />
        )}
      </section>
      <ShopStatsPanel onLoaded={onStatsLoaded} />
    </>
  )
}

function SellerDashboard() {
  const [statsUpdatedAt, setStatsUpdatedAt] = useState<Date>()
  return (
    <>
      <div className="flex flex-wrap items-center justify-between gap-x-5 gap-y-3">
        <div>
          <h1 className="text-[22px] font-bold leading-snug tracking-tight sm:text-2xl">Tổng quan gian hàng</h1>
          <p className="mt-1 text-[13px] leading-relaxed text-slate-500 dark:text-slate-400">Theo dõi đơn hàng và doanh thu của gian hàng.</p>
        </div>
        {statsUpdatedAt && (
          <span className="inline-flex items-center gap-1.5 rounded-full border border-slate-200/60 bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300">
            <span aria-hidden="true" className="size-1.5 rounded-full bg-emerald-500 dark:bg-emerald-400" />
            <span>Cập nhật lúc <time dateTime={statsUpdatedAt.toISOString()}>{updateTime.format(statsUpdatedAt)}</time></span>
          </span>
        )}
      </div>
      <ShopOverview onStatsLoaded={setStatsUpdatedAt} />
    </>
  )
}

export default function SellerShopPage() {
  const { user } = useAuth()
  if (!user) return null
  return (
    <AppShell>
      <SellerDashboard key={user.id} />
    </AppShell>
  )
}
