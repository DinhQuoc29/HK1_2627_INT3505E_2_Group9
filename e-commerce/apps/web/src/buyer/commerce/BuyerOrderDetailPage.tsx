import { useCallback, useState } from 'react'
import { Link, useLocation, useParams } from 'react-router-dom'
import { ApiError, api, type Order } from '../../shared/api/client'
import { Alert } from '../../shared/auth/components/ui'
import { OrderDetails } from '../../shared/orders/OrderDetails'
import { OrderBadge, orderMoney, orderPanel, orderSecondary } from '../../shared/orders/orderUi'
import { BuyerStoreLayout } from '../../shared/layout/BuyerStoreLayout'
import { BuyerLoading, BuyerRequestError, buyerLink } from '../BuyerFeedback'
import { buyerErrorMessage, useBuyerRequest } from '../useBuyerRequest'

const dangerButton = 'inline-flex min-h-11 items-center justify-center rounded-xl bg-red-700 px-4 py-2 text-sm font-semibold text-white hover:bg-red-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-red-600 disabled:opacity-50'

export default function BuyerOrderDetailPage() {
  const { orderId = '' } = useParams()
  const { search } = useLocation()

  return (
    <BuyerStoreLayout>
      <div className="mx-auto max-w-5xl space-y-5 px-4 py-7 sm:px-6 sm:py-10">
        <Link to={`/orders${search}`} className={buyerLink}>← Quay lại đơn mua</Link>
        <h1 className="text-3xl font-bold tracking-tight">Chi tiết đơn hàng</h1>
        <OrderLoader key={orderId} id={orderId} />
      </div>
    </BuyerStoreLayout>
  )
}

function OrderLoader({ id }: { id: string }) {
  const load = useCallback(() => api.order(id), [id])
  const { state, retry } = useBuyerRequest(load)
  if (state.status === 'loading') return <BuyerLoading label="Đang tải chi tiết đơn hàng…" />
  if (state.status === 'error') {
    const unavailable = state.error instanceof ApiError && [403, 404, 422].includes(state.error.status)
    return <BuyerRequestError message={buyerErrorMessage(state.error, 'Không tải được chi tiết đơn hàng.')} retry={unavailable ? undefined : retry} />
  }
  return <BuyerOrder initial={state.data} />
}

function BuyerOrder({ initial }: { initial: Order }) {
  const [order, setOrder] = useState(initial)
  const [confirming, setConfirming] = useState(false)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState<{ tone: 'success' | 'error'; text: string }>()
  const canCancel = order.status === 'pending_payment' || order.status === 'paid'
  const refunded = order.refunded_amount ?? 0

  function applyCancellation(updated: Order) {
    setOrder(updated)
    setConfirming(false)
    setMessage({ tone: 'success', text: 'Đơn hàng đã được hủy.' })
  }

  async function cancel() {
    if (saving || !canCancel) return
    setSaving(true)
    setMessage(undefined)
    try {
      applyCancellation(await api.cancelOrder(order.id))
    } catch (error) {
      if (error instanceof ApiError && (error.slug === 'invalid-order-transition' || error.status === 0 || error.status >= 500)) {
        const latest = await api.order(order.id).catch(() => null)
        if (latest?.status === 'cancelled') {
          applyCancellation(latest)
          return
        }
        if (latest) {
          setOrder(latest)
          setConfirming(false)
        }
      }
      setMessage({ tone: 'error', text: buyerErrorMessage(error, 'Không thể hủy đơn. Hãy thử lại.') })
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-4">
      {message && <Alert tone={message.tone}>{message.text}</Alert>}
      <section className={`${orderPanel} space-y-4`} aria-label="Trạng thái đơn hàng">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0 space-y-1">
            <h2 className="wrap-anywhere text-xl font-bold">{order.shop.name}</h2>
            <p className="break-all text-sm text-zinc-500">Mã đơn {order.id}</p>
          </div>
          <OrderBadge status={order.status} />
        </div>
        {order.status === 'cancelled' && (
          <div className="space-y-1 text-sm text-zinc-700 dark:text-zinc-300">
            <p>{order.cancelled_by === 'seller' ? 'Gian hàng đã hủy đơn.' : 'Người mua đã hủy đơn.'}</p>
            {refunded > 0 && <p>Đã hoàn mô phỏng <strong>{orderMoney.format(refunded)}</strong></p>}
          </div>
        )}
        <div className="flex flex-wrap items-center gap-2">
          <Link to={`/checkout/${order.checkout_id}`} className={buyerLink}>Xem thông tin thanh toán</Link>
          {canCancel && !confirming && (
            <button type="button" className={orderSecondary} onClick={() => { setMessage(undefined); setConfirming(true) }}>Hủy đơn</button>
          )}
        </div>
        {canCancel && confirming && (
          <section aria-labelledby="confirm-order-cancellation" className="space-y-3 rounded-xl border border-red-200 bg-red-50 p-4 text-sm dark:border-red-900 dark:bg-red-950/30">
            <h3 id="confirm-order-cancellation" className="font-semibold">Hủy đơn của {order.shop.name}?</h3>
            <p>{order.status === 'paid'
              ? `Bạn sẽ được hoàn mô phỏng ${orderMoney.format(order.total_amount)} cho đơn này.`
              : 'Đơn chưa thanh toán sẽ được hủy.'}</p>
            <div className="flex flex-wrap gap-2">
              <button type="button" className={dangerButton} disabled={saving} onClick={cancel}>{saving ? 'Đang hủy…' : 'Xác nhận hủy đơn'}</button>
              <button type="button" className={orderSecondary} disabled={saving} onClick={() => setConfirming(false)}>Giữ đơn</button>
            </div>
          </section>
        )}
      </section>
      <OrderDetails order={order} />
    </div>
  )
}
