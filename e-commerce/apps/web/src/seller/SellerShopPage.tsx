import { useEffect, useState } from 'react'
import { ApiError, api, type Shop } from '../shared/api/client'
import { useAuth } from '../shared/auth/AuthContext'
import { AppShell } from '../shared/layout/AppShell'
import { Alert, Button, Spinner } from '../shared/auth/components/ui'
import { describeError } from '../shared/auth/errors'
import { orderSecondary } from './orders/orderUi'
import { ShopEditor } from './shop/ShopEditor'
import { ShopStatsPanel } from './shop/ShopStatsPanel'

type ShopState =
  | { status: 'loading' }
  | { status: 'ready'; shop: Shop }
  | { status: 'error'; message: string; canRetry: boolean }

const shopDate = new Intl.DateTimeFormat('vi-VN', { dateStyle: 'medium', timeZone: 'Asia/Ho_Chi_Minh' })

function ShopOverview() {
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

  if (state.status === 'loading') return <Spinner label="Đang tải shop…" />

  if (state.status === 'error') {
    const retry = () => {
      setState({ status: 'loading' })
      setAttempt((previous) => previous + 1)
    }
    return (
      <div className="space-y-4">
        <Alert>{state.message}</Alert>
        {state.canRetry && (
          <div className="w-fit">
            <Button type="button" onClick={retry}>Thử lại</Button>
          </div>
        )}
      </div>
    )
  }

  const { shop } = state
  return (
    <>
      {notice && <Alert tone="success">{notice}</Alert>}
      <section
        aria-label="Thông tin shop"
        className="min-w-0 rounded-2xl border border-zinc-200 border-t-4 border-t-brand-500 bg-white p-5 shadow-sm sm:p-7 dark:border-zinc-800 dark:border-t-brand-500 dark:bg-zinc-900"
      >
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="min-w-0 text-xl font-semibold tracking-tight wrap-anywhere sm:text-2xl">{shop.name}</h2>
          {!editing && (
            <button type="button" className={orderSecondary} onClick={() => { setNotice(undefined); setEditing(true) }}>
              Chỉnh sửa thông tin
            </button>
          )}
        </div>
        <dl className="mt-5 grid gap-4 border-t border-zinc-200 pt-5 text-sm sm:grid-cols-2 dark:border-zinc-800">
          <div>
            <dt className="text-zinc-500 dark:text-zinc-400">Nơi bán</dt>
            <dd className="mt-1 font-medium">{shop.province.name}</dd>
          </div>
          <div>
            <dt className="text-zinc-500 dark:text-zinc-400">Mở shop từ</dt>
            <dd className="mt-1 font-medium">
              <time dateTime={shop.created_at}>{shopDate.format(new Date(shop.created_at))}</time>
            </dd>
          </div>
        </dl>
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
      <ShopStatsPanel />
    </>
  )
}

export default function SellerShopPage() {
  const { user } = useAuth()
  if (!user) return null
  return (
    <AppShell>
      <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">Tổng quan</h1>
      <ShopOverview key={user.id} />
    </AppShell>
  )
}
