import { useEffect, useState } from 'react'
import { useLocation, useSearchParams } from 'react-router-dom'
import { api, type OrderStatus, type SellerOrderPage, type ShopStatistics } from '../../shared/api/client'
import { Alert, Spinner } from '../../shared/auth/components/ui'
import { describeError } from '../../shared/auth/errors'
import { AppShell } from '../../shared/layout/AppShell'
import { orderStatusOptions } from '../../shared/orders/orderUi'
import { SellerIcon } from '../sellerUi'
import { SellerOrderTable } from './SellerOrderTable'

const panel = 'min-w-0 rounded-lg border border-slate-200 bg-white shadow-xs'
const focus = 'focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-(--seller-accent)'
const secondary = `inline-flex min-h-10 items-center gap-1.5 rounded-md border border-slate-200 bg-white px-3 text-[13px] font-medium text-slate-700 hover:bg-slate-50 ${focus}`
const number = new Intl.NumberFormat('vi-VN')

function searchable(text: string) {
  return text.trim().toLocaleLowerCase('vi-VN').normalize('NFD').replace(/\p{M}/gu, '').replace(/đ/g, 'd')
}

function StatusFilter({ status, stats, onChange }: { status?: OrderStatus; stats?: ShopStatistics; onChange: (value: string) => void }) {
  const filters = [
    { value: '', label: 'Tất cả', count: stats?.total_orders },
    ...orderStatusOptions.map(([value, { label }]) => ({ value, label, count: stats?.orders_by_status[value] })),
  ]
  return (
    <div className="border-b border-slate-200 px-3.5 @min-[40rem]:px-4">
      <div role="group" aria-label="Lọc theo trạng thái đơn hàng" className="hidden flex-wrap gap-x-3 @min-[40rem]:flex">
        {filters.map(({ value, label, count }) => {
          const active = value === (status ?? '')
          return (
            <button
              key={value}
              type="button"
              aria-pressed={active}
              className={`flex min-h-12 items-center gap-1.5 border-b-2 px-1 text-[13px] font-medium transition-colors ${focus} ${active
                ? 'border-(--seller-accent) text-brand-700'
                : 'border-transparent text-slate-600 hover:text-slate-900'}`}
              onClick={() => onChange(value)}
            >
              {label}
              {count !== undefined && (
                <span aria-hidden="true" className={`rounded-full px-1.5 py-0.5 text-[11px] tabular-nums ${active ? 'bg-(--seller-nav-active)' : 'bg-slate-100 text-slate-500'}`}>{number.format(count)}</span>
              )}
            </button>
          )
        })}
      </div>
      <div className="grid gap-1.5 py-3 @min-[40rem]:hidden">
        <label htmlFor="order-status" className="text-xs font-medium text-slate-600">Trạng thái đơn hàng</label>
        <select id="order-status" className={`min-h-11 w-full rounded-md border border-slate-200 bg-white px-3 text-[13px] text-slate-700 ${focus}`} value={status ?? ''} onChange={(event) => onChange(event.target.value)}>
          {filters.map(({ value, label, count }) => (
            <option key={value} value={value}>{value ? label : 'Tất cả trạng thái'}{count === undefined ? '' : ` (${number.format(count)})`}</option>
          ))}
        </select>
      </div>
    </div>
  )
}

function OrderList({ status, stats, query, onStatusChange }: {
  status?: OrderStatus
  stats?: ShopStatistics
  query: string
  onStatusChange: (value: string) => void
}) {
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

  const term = searchable(query).replace(/^#/, '')
  const orders = result?.items.filter(({ id, shipping }) => !term || id.toLowerCase().includes(term) || searchable(shipping.name).includes(term)) ?? []

  return (
    <section aria-label="Quản lý đơn hàng" className={`@container overflow-hidden ${panel}`}>
      <StatusFilter status={status} stats={stats} onChange={onStatusChange} />
      {orders.length ? (
        <SellerOrderTable orders={orders} statusSearch={status ? `?status=${status}` : ''} query={query} />
      ) : !loading && !error && (
        <div className="px-4 py-10 text-center">
          <p className="text-sm font-semibold">{term ? 'Không tìm thấy đơn hàng phù hợp.' : status ? 'Không có đơn hàng ở trạng thái này.' : 'Gian hàng chưa có đơn hàng.'}</p>
          <p className="mt-1 text-[13px] text-slate-500">
            {term
              ? result?.next_cursor ? 'Thử từ khóa khác hoặc tải thêm đơn hàng để tìm tiếp.' : 'Thử tìm bằng mã đơn hoặc tên người nhận khác.'
              : status ? 'Hãy chọn trạng thái khác để xem thêm đơn.' : 'Đơn phát sinh sẽ xuất hiện tại đây.'}
          </p>
        </div>
      )}
      {loading && <div className="p-4"><Spinner label="Đang tải đơn hàng…" /></div>}
      {error && (
        <div className="space-y-3 p-4">
          <Alert>{error}</Alert>
          <button type="button" className={secondary} onClick={() => { startLoading(); setAttempt((count) => count + 1) }}>Thử lại</button>
        </div>
      )}
      {result && (
        <div className="flex flex-wrap items-center justify-between gap-2 border-t border-slate-200 bg-slate-50/80 px-4 py-2.5">
          <p className="text-xs text-slate-500">
            Hiển thị <strong className="font-semibold text-slate-700">{number.format(orders.length)}</strong>
            {term ? ` trên ${number.format(result.items.length)} đơn đã tải` : ' đơn hàng'}
          </p>
          {!loading && !error && result.next_cursor && (
            <button type="button" className={secondary} onClick={() => { startLoading(); setCursor(result.next_cursor ?? undefined) }}>
              Tải thêm đơn hàng <SellerIcon name="chevron" className="size-4" />
            </button>
          )}
        </div>
      )}
    </section>
  )
}

export default function SellerOrdersPage() {
  const [params, setParams] = useSearchParams()
  const { state } = useLocation()
  const value = params.get('status')
  const status = orderStatusOptions.find(([key]) => key === value)?.[0]
  const query = typeof state?.orderQuery === 'string' ? state.orderQuery : ''
  const [search, setSearch] = useState(query)
  const [stats, setStats] = useState<ShopStatistics>()

  useEffect(() => { setSearch(query) }, [query])

  useEffect(() => {
    let cancelled = false
    api.shopStatistics().then((data) => {
      if (!cancelled) setStats(data)
    }, () => { /* The status filter remains available when counts cannot be loaded. */ })
    return () => { cancelled = true }
  }, [])

  const changeStatus = (next: string) => {
    const updated = new URLSearchParams(params)
    if (next) updated.set('status', next)
    else updated.delete('status')
    setParams(updated, { replace: true, state: { orderQuery: query } })
  }

  return (
    <AppShell>
      <div>
        <h1 className="text-[22px] leading-7 font-semibold tracking-tight">Đơn hàng</h1>
        <p className="mt-0.5 text-[13px] leading-5 text-slate-500">Xem đơn của gian hàng và cập nhật tiến trình giao hàng.</p>
      </div>
      <form
        aria-label="Tìm đơn hàng"
        className={`flex flex-wrap items-center justify-between gap-2 p-3 ${panel}`}
        onSubmit={(event) => { event.preventDefault(); setParams(params, { replace: true, state: { orderQuery: search.trim() } }) }}
      >
        <div className="flex min-w-0 flex-1 basis-[24rem] gap-2">
          <div className="relative min-w-0 flex-1">
            <SellerIcon name="search" className="pointer-events-none absolute top-1/2 left-3 size-[18px] -translate-y-1/2 text-slate-400" />
            <input
              type="search" aria-label="Mã đơn hoặc tên người nhận" aria-describedby="order-search-scope"
              placeholder="Tìm mã đơn, tên người nhận…" maxLength={120} value={search} onChange={(event) => setSearch(event.target.value)}
              className={`min-h-11 w-full rounded-md border border-slate-200 bg-white pr-3 pl-9 text-[13px] placeholder:text-slate-500 sm:min-h-9 ${focus}`}
            />
          </div>
          <button type="submit" className={`min-h-11 shrink-0 rounded-md bg-slate-900 px-3.5 text-[13px] font-medium text-white transition-colors hover:bg-slate-800 sm:min-h-9 ${focus}`}>Tìm kiếm</button>
        </div>
        <p id="order-search-scope" className="px-1 text-xs text-slate-500">Tìm trong các đơn đã tải</p>
      </form>
      <OrderList
        key={status ?? 'all'}
        status={status}
        stats={stats}
        query={query}
        onStatusChange={changeStatus}
      />
    </AppShell>
  )
}
