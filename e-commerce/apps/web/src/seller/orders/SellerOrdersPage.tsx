import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api, type OrderStatus, type SellerOrderPage } from '../../shared/api/client'
import { Alert, Spinner } from '../../shared/auth/components/ui'
import { describeError } from '../../shared/auth/errors'
import { AppShell } from '../../shared/layout/AppShell'
import { OrderBadge, orderDate, orderMoney, orderPanel, orderSecondary, orderStatusOptions } from '../../shared/orders/orderUi'

function OrderList({ status }: { status?: OrderStatus }) {
  const [result, setResult] = useState<SellerOrderPage>()
  const [error, setError] = useState<string>()
  const [cursor, setCursor] = useState<string>()
  const [loading, setLoading] = useState(true)
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    let cancelled = false
    api.sellerOrders({ status, cursor }).then(
      (page) => {
        if (cancelled) return
        setResult((previous) => {
          if (!cursor || !previous) return page
          const seen = new Set(previous.items.map(({ id }) => id))
          return { items: [...previous.items, ...page.items.filter(({ id }) => !seen.has(id))], next_cursor: page.next_cursor }
        })
        setLoading(false)
      },
      (failure) => {
        if (cancelled) return
        setError(describeError(failure).message ?? 'Không tải được đơn hàng.')
        setLoading(false)
      },
    )
    return () => { cancelled = true }
  }, [status, cursor, attempt])

  const startLoading = () => {
    setError(undefined)
    setLoading(true)
  }

  return (
    <>
      {result?.items.length ? (
        <ul aria-label="Danh sách đơn hàng" className="divide-y divide-zinc-200 rounded-2xl border border-zinc-200 bg-white shadow-sm dark:divide-zinc-800 dark:border-zinc-800 dark:bg-zinc-900">
          {result.items.map((order) => (
            <li key={order.id}>
              <Link
                to={`/seller/orders/${order.id}${status ? `?status=${status}` : ''}`}
                className="grid gap-3 rounded-2xl p-4 hover:bg-zinc-50 focus-visible:z-10 focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-brand-500 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center dark:hover:bg-zinc-800/60"
              >
                <div className="min-w-0">
                  <h2 className="font-semibold">Đơn #{order.id.slice(0, 8).toUpperCase()}</h2>
                  <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">
                    <time dateTime={order.created_at}>{orderDate.format(new Date(order.created_at))}</time>
                    {' · '}{order.items.reduce((total, item) => total + item.quantity, 0)} sản phẩm
                  </p>
                </div>
                <div className="flex flex-wrap items-center gap-x-3 gap-y-2 sm:justify-end">
                  <OrderBadge status={order.status} />
                  <strong className="text-sm tabular-nums">{orderMoney.format(order.total_amount)}</strong>
                  <span className="text-xs font-semibold text-brand-700 dark:text-brand-100">Xem chi tiết <span aria-hidden="true">→</span></span>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      ) : !loading && !error && (
        <div className={`${orderPanel} py-9 text-center`}>
          <p className="font-semibold">{status ? 'Không có đơn hàng ở trạng thái này.' : 'Gian hàng chưa có đơn hàng.'}</p>
          <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">
            {status ? 'Hãy chọn trạng thái khác để xem thêm đơn.' : 'Đơn phát sinh sẽ xuất hiện tại đây.'}
          </p>
        </div>
      )}
      {loading && <div className={orderPanel}><Spinner label="Đang tải đơn hàng…" /></div>}
      {error && (
        <div className="space-y-3">
          <Alert>{error}</Alert>
          <button type="button" className={orderSecondary} onClick={() => { startLoading(); setAttempt((count) => count + 1) }}>Thử lại</button>
        </div>
      )}
      {!loading && !error && result?.next_cursor && (
        <div className="flex justify-end">
          <button type="button" className={orderSecondary} onClick={() => { startLoading(); setCursor(result.next_cursor ?? undefined) }}>Tải thêm đơn hàng</button>
        </div>
      )}
    </>
  )
}

export default function SellerOrdersPage() {
  const [params, setParams] = useSearchParams()
  const value = params.get('status')
  const status = orderStatusOptions.find(([key]) => key === value)?.[0]

  return (
    <AppShell>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">Đơn hàng</h1>
          <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">Xem đơn của gian hàng và cập nhật tiến trình giao hàng.</p>
        </div>
        <div className="w-full sm:w-auto">
          <label htmlFor="order-status" className="mb-1.5 block text-sm font-medium">Trạng thái đơn hàng</label>
          <select
            id="order-status"
            className="min-h-11 w-full rounded-xl border border-zinc-300 bg-white px-3 text-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-500 sm:min-w-44 dark:border-zinc-700 dark:bg-zinc-900"
            value={status ?? ''}
            onChange={(event) => setParams(event.target.value ? { status: event.target.value } : {}, { replace: true })}
          >
            <option value="">Tất cả trạng thái</option>
            {orderStatusOptions.map(([key, { label }]) => <option key={key} value={key}>{label}</option>)}
          </select>
        </div>
      </div>
      <OrderList key={status ?? 'all'} status={status} />
    </AppShell>
  )
}
