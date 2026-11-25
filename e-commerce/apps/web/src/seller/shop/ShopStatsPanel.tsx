import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, type ShopStatistics } from '../../shared/api/client'
import { Alert, Spinner } from '../../shared/auth/components/ui'
import { describeError } from '../../shared/auth/errors'
import { orderMoney, orderPanel, orderSecondary, orderStatusOptions } from '../orders/orderUi'

const count = new Intl.NumberFormat('vi-VN')

export function ShopStatsPanel() {
  const [stats, setStats] = useState<ShopStatistics>()
  const [error, setError] = useState<string>()
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    let cancelled = false
    api.shopStatistics().then(
      (result) => { if (!cancelled) setStats(result) },
      (failure) => { if (!cancelled) setError(describeError(failure).message ?? 'Không tải được thống kê gian hàng.') },
    )
    return () => { cancelled = true }
  }, [attempt])

  return (
    <section aria-labelledby="shop-statistics" className={orderPanel}>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 id="shop-statistics" className="text-lg font-semibold">Thống kê gian hàng</h2>
          <p className="mt-0.5 text-sm text-zinc-600 dark:text-zinc-400">Toàn thời gian</p>
        </div>
        <Link to="/seller/orders" className={orderSecondary}>Xem tất cả đơn</Link>
      </div>
      {error ? (
        <div className="space-y-3">
          <Alert>{error}</Alert>
          <button type="button" className={orderSecondary} onClick={() => { setError(undefined); setAttempt((value) => value + 1) }}>
            Tải lại thống kê
          </button>
        </div>
      ) : stats ? (
        <div className="space-y-4">
          <dl className="grid gap-3 sm:grid-cols-2">
            <div className="min-w-0 rounded-xl bg-zinc-50 p-4 dark:bg-zinc-800/60">
              <dt className="text-sm text-zinc-600 dark:text-zinc-400">Tổng số đơn</dt>
              <dd className="mt-1 text-2xl font-semibold tabular-nums">{count.format(stats.total_orders)}</dd>
            </div>
            <div className="min-w-0 rounded-xl bg-brand-50 p-4 dark:bg-brand-900/25">
              <dt className="text-sm font-medium text-brand-900 dark:text-brand-100">Doanh thu ghi nhận</dt>
              <dd className="mt-1 text-2xl font-semibold tabular-nums wrap-anywhere">{orderMoney.format(BigInt(stats.recorded_revenue_vnd))}</dd>
              <dd className="mt-1 text-xs leading-relaxed text-zinc-700 dark:text-zinc-300">
                {stats.captured_orders
                  ? `Thanh toán mô phỏng của ${count.format(stats.captured_orders)} đơn, đã loại trừ khoản hoàn.`
                  : 'Chưa có khoản thanh toán mô phỏng được ghi nhận.'}
              </dd>
            </div>
          </dl>
          <ul aria-label="Số đơn theo trạng thái" className="grid grid-cols-2 gap-2 sm:grid-cols-3 xl:grid-cols-5">
            {orderStatusOptions.map(([status, { label }]) => (
              <li key={status} className="min-w-0">
                <Link
                  to={`/seller/orders?status=${status}`}
                  aria-label={`${label}: ${count.format(stats.orders_by_status[status])} đơn`}
                  className="block h-full rounded-xl border border-zinc-200 p-3 hover:bg-zinc-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-500 dark:border-zinc-700 dark:hover:bg-zinc-800"
                >
                  <span className="block text-xs text-zinc-600 dark:text-zinc-400">{label}</span>
                  <span className="mt-1 block text-lg font-semibold tabular-nums">{count.format(stats.orders_by_status[status])}</span>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      ) : <Spinner label="Đang tải thống kê…" />}
    </section>
  )
}
