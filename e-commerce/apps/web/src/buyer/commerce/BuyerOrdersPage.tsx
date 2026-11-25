import { useCallback, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api, type OrderPage, type OrderStatus } from '../../shared/api/client'
import { Alert, SelectField } from '../../shared/auth/components/ui'
import { OrderBadge, orderDate, orderMoney, orderPanel, orderSecondary, orderStatusOptions } from '../../shared/orders/orderUi'
import { BuyerStoreLayout } from '../../shared/layout/BuyerStoreLayout'
import { BuyerEmptyState, BuyerLoading, BuyerRequestError, buyerLink } from '../BuyerFeedback'
import { buyerErrorMessage, useBuyerRequest } from '../useBuyerRequest'

const statusOptions = orderStatusOptions.map(([value, { label }]) => ({ value, label }))

export default function BuyerOrdersPage() {
  const [params, setParams] = useSearchParams()
  const status = statusOptions.find(({ value }) => value === params.get('status'))?.value

  return (
    <BuyerStoreLayout>
      <div className="mx-auto max-w-5xl space-y-5 px-4 py-7 sm:px-6 sm:py-10">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <h1 className="text-3xl font-bold tracking-tight">Đơn mua</h1>
          <SelectField
            className="w-full sm:w-auto"
            label="Trạng thái đơn hàng"
            placeholder="Tất cả trạng thái"
            options={statusOptions}
            value={status ?? ''}
            onChange={(event) => setParams(event.target.value ? { status: event.target.value } : {})}
          />
        </div>
        <OrderHistory key={status ?? 'all'} status={status} />
      </div>
    </BuyerStoreLayout>
  )
}

function OrderHistory({ status }: { status?: OrderStatus }) {
  const load = useCallback(() => api.buyerOrders({ status }), [status])
  const { state, retry } = useBuyerRequest(load)

  if (state.status === 'loading') return <BuyerLoading label="Đang tải đơn mua…" />
  if (state.status === 'error') {
    return <BuyerRequestError message={buyerErrorMessage(state.error, 'Không tải được đơn mua.')} retry={retry} />
  }
  if (!state.data.items.length) {
    return (
      <BuyerEmptyState title={status ? 'Không có đơn ở trạng thái này' : 'Bạn chưa có đơn mua'}>
        <Link to={status ? '/orders' : '/products'} className={buyerLink}>
          {status ? 'Xem tất cả đơn' : 'Khám phá sản phẩm'}
        </Link>
      </BuyerEmptyState>
    )
  }
  return <OrderList initial={state.data} status={status} />
}

function OrderList({ initial, status }: { initial: OrderPage; status?: OrderStatus }) {
  const [page, setPage] = useState(initial)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function loadMore() {
    if (!page.next_cursor || loading) return
    setLoading(true)
    setError('')
    try {
      const next = await api.buyerOrders({ status, cursor: page.next_cursor })
      setPage((previous) => {
        const ids = new Set(previous.items.map(({ id }) => id))
        return { items: [...previous.items, ...next.items.filter(({ id }) => !ids.has(id))], next_cursor: next.next_cursor }
      })
    } catch (failure) {
      setError(buyerErrorMessage(failure, 'Không tải được các đơn tiếp theo.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <ul aria-label="Đơn mua theo shop" className="space-y-3">
        {page.items.map((order) => (
          <li key={order.id}>
            <Link
              to={`/orders/${order.id}${status ? `?status=${status}` : ''}`}
              className={`${orderPanel} block space-y-3 hover:border-brand-500 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-500`}
            >
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div className="min-w-0">
                  <h2 className="wrap-anywhere font-semibold">{order.shop.name}</h2>
                  <p className="mt-1 text-sm text-zinc-500">
                    Đơn #{order.id.slice(0, 8).toUpperCase()} · <time dateTime={order.created_at}>{orderDate.format(new Date(order.created_at))}</time>
                  </p>
                </div>
                <OrderBadge status={order.status} />
              </div>
              <div className="flex flex-wrap items-baseline justify-between gap-2 border-t border-zinc-200 pt-3 text-sm dark:border-zinc-800">
                <p className="wrap-anywhere text-zinc-600 dark:text-zinc-300">
                  {order.items[0]?.product_name}
                  {order.items.length > 1 && ` và ${order.items.length - 1} sản phẩm khác`}
                </p>
                <strong>{orderMoney.format(order.total_amount)}</strong>
              </div>
            </Link>
          </li>
        ))}
      </ul>
      {error && <Alert>{error}</Alert>}
      {page.next_cursor && (
        <button type="button" className={orderSecondary} disabled={loading} onClick={loadMore}>
          {loading ? 'Đang tải…' : 'Tải thêm đơn mua'}
        </button>
      )}
    </div>
  )
}
