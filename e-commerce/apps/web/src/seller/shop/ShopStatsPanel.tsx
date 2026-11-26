import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, type ShopStatistics } from '../../shared/api/client'
import { Alert, Spinner } from '../../shared/auth/components/ui'
import { describeError } from '../../shared/auth/errors'
import { orderMoney, orderSecondary, orderStatusOptions } from '../../shared/orders/orderUi'
import { SellerIcon, sellerCard, sellerTextLink } from '../sellerUi'

const count = new Intl.NumberFormat('vi-VN')
const metricLabel = 'text-[13px] font-semibold tracking-wide text-slate-600 uppercase dark:text-slate-300'
const metricPeriod = 'shrink-0 rounded-md border border-slate-200/60 bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300'
const metricValue = 'text-3xl font-bold leading-tight tracking-tight tabular-nums wrap-anywhere sm:text-[32px]'

export function ShopStatsPanel({ onLoaded }: { onLoaded: (updatedAt: Date) => void }) {
  const [stats, setStats] = useState<ShopStatistics>()
  const [error, setError] = useState<string>()
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    let cancelled = false
    api.shopStatistics().then(
      (result) => {
        if (cancelled) return
        setStats(result)
        onLoaded(new Date())
      },
      (failure) => { if (!cancelled) setError(describeError(failure).message ?? 'Không tải được thống kê gian hàng.') },
    )
    return () => { cancelled = true }
  }, [attempt, onLoaded])

  return (
    <>
      {stats && (
        <div className="grid gap-4 md:grid-cols-2">
          <section className={`${sellerCard} flex flex-col gap-3`}>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h2 className={metricLabel}>Tổng số đơn</h2>
              <span className={metricPeriod}>Toàn thời gian</span>
            </div>
            <div className="flex flex-wrap items-baseline gap-x-2">
              <span className={metricValue}>{count.format(stats.total_orders)}</span>
              <span className="text-sm text-slate-500 dark:text-slate-400">đơn hàng</span>
            </div>
            <div className="mt-auto flex justify-end border-t border-slate-100 pt-2 dark:border-slate-800">
              <Link to="/seller/orders" className={sellerTextLink}>Chi tiết đơn hàng <SellerIcon name="chevron" className="size-3.5" /></Link>
            </div>
          </section>

          <section className={`${sellerCard} flex flex-col gap-3`}>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h2 className={metricLabel}>Doanh thu ghi nhận</h2>
              <span className={metricPeriod}>Toàn thời gian</span>
            </div>
            <p className={metricValue}>{orderMoney.format(BigInt(stats.recorded_revenue_vnd))}</p>
            <p className="flex items-start gap-2 rounded-lg border border-slate-100 bg-slate-50 px-3 py-2.5 text-xs leading-relaxed text-slate-500 dark:border-slate-700 dark:bg-slate-800/60 dark:text-slate-300">
              <SellerIcon name="info" className="mt-0.5 size-4 text-slate-400" />
              <span>{stats.captured_orders
                ? `Thanh toán mô phỏng của ${count.format(stats.captured_orders)} đơn, đã loại trừ khoản hoàn.`
                : 'Chưa có khoản thanh toán mô phỏng được ghi nhận.'}</span>
            </p>
          </section>
        </div>
      )}

      <section aria-labelledby="shop-statistics" className={sellerCard}>
        <div className="mb-4 flex flex-wrap items-center justify-between gap-x-4 gap-y-1 border-b border-slate-100 pb-2 dark:border-slate-800">
          <h2 id="shop-statistics" className="text-base font-bold">Thống kê đơn hàng</h2>
          <Link to="/seller/orders" className={sellerTextLink}>Xem tất cả đơn <SellerIcon name="arrow" className="size-4" /></Link>
        </div>
        {stats ? (
          <ul aria-label="Số đơn theo trạng thái" className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-5">
            {orderStatusOptions.map(([status, { label }]) => {
              const total = count.format(stats.orders_by_status[status])
              const needsShipping = status === 'paid' && stats.orders_by_status[status] > 0
              return (
                <li key={status} className="min-w-0 last:col-span-2 sm:last:col-span-1">
                  <Link
                    to={`/seller/orders?status=${status}`}
                    aria-label={`${label}: ${total} đơn`}
                    className={`flex h-full min-h-19 flex-col items-center justify-center gap-1 rounded-lg border p-3 text-center transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-(--seller-accent) ${
                      needsShipping
                        ? 'border-(--seller-status-border) bg-(--seller-status-bg) text-(--seller-accent) hover:bg-(--seller-nav-active)'
                        : 'border-slate-100 bg-slate-50 text-slate-800 hover:bg-slate-100/70 dark:border-slate-700 dark:bg-slate-800/60 dark:text-slate-300 dark:hover:bg-slate-800'
                    }`}
                  >
                    <span className="text-xl font-bold leading-tight tabular-nums">{total}</span>
                    <span className={`text-xs font-medium ${needsShipping ? '' : 'text-slate-500 dark:text-slate-400'}`}>{label}</span>
                  </Link>
                </li>
              )
            })}
          </ul>
        ) : error ? (
          <div className="space-y-3">
            <Alert>{error}</Alert>
            <button type="button" className={orderSecondary} onClick={() => { setError(undefined); setAttempt((value) => value + 1) }}>
              Tải lại thống kê
            </button>
          </div>
        ) : <Spinner label="Đang tải thống kê…" />}
      </section>
    </>
  )
}
