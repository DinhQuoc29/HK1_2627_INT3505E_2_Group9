import { useCallback } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ApiError, api, type CheckoutResult } from '../../shared/api/client'
import { Alert } from '../../shared/auth/components/ui'
import { BuyerStoreLayout } from '../../shared/layout/BuyerStoreLayout'
import { productPrice } from '../catalog/catalogUi'
import { BuyerLoading, BuyerRequestError, buyerLink } from '../BuyerFeedback'
import { buyerErrorMessage, useBuyerRequest } from '../useBuyerRequest'

const paymentLabels = {
  pending: 'Đang chờ thanh toán',
  succeeded: 'Thanh toán mô phỏng thành công',
  failed: 'Thanh toán mô phỏng thất bại',
  cancelled: 'Thanh toán đã bị hủy',
}

export default function BuyerCheckoutResultPage() {
  const { checkoutId = '' } = useParams()
  return (
    <BuyerStoreLayout>
      <div className="mx-auto max-w-5xl space-y-5 px-4 py-7 sm:px-6 sm:py-10">
        <h1 className="text-3xl font-bold tracking-tight">Kết quả thanh toán</h1>
        <ReceiptLoader key={checkoutId} id={checkoutId} />
        <div className="flex flex-wrap gap-2">
          <Link to="/orders" className={buyerLink}>Xem đơn mua</Link>
          <Link to="/products" className={buyerLink}>Tiếp tục mua sắm</Link>
        </div>
      </div>
    </BuyerStoreLayout>
  )
}

function ReceiptLoader({ id }: { id: string }) {
  const load = useCallback(() => api.checkoutResult(id), [id])
  const { state, retry } = useBuyerRequest(load)
  if (state.status === 'loading') return <BuyerLoading label="Đang tải kết quả thanh toán…" />
  if (state.status === 'error') {
    const unavailable = state.error instanceof ApiError && [403, 404, 422].includes(state.error.status)
    return <BuyerRequestError message={buyerErrorMessage(state.error, 'Không tải được kết quả thanh toán.')} retry={unavailable ? undefined : retry} />
  }
  return <Receipt result={state.data} />
}

function Receipt({ result }: { result: CheckoutResult }) {
  const { payment, orders } = result
  const allocations = new Map(payment.allocations.map((allocation) => [allocation.order_id, allocation]))
  const shipping = orders[0]?.shipping

  return (
    <div className="space-y-5">
      <Alert tone={payment.status === 'succeeded' ? 'success' : 'info'}>{paymentLabels[payment.status]}</Alert>
      <dl className="grid grid-cols-1 gap-4 rounded-2xl border border-zinc-200 bg-white p-4 wrap-anywhere sm:grid-cols-2 sm:p-5 dark:border-zinc-800 dark:bg-zinc-900">
        <div><dt className="text-sm text-zinc-500">Mã lượt mua</dt><dd className="break-all font-medium">{result.id}</dd></div>
        <div><dt className="text-sm text-zinc-500">Mã thanh toán</dt><dd className="break-all font-medium">{payment.id}</dd></div>
        <div><dt className="text-sm text-zinc-500">Tổng đơn hàng</dt><dd className="font-bold">{productPrice.format(result.total_amount)}</dd></div>
        {payment.status === 'succeeded' && (
          <div><dt className="text-sm text-zinc-500">Đã thanh toán mô phỏng</dt><dd className="font-bold">{productPrice.format(payment.amount)}</dd></div>
        )}
        {shipping && (
          <div className="sm:col-span-2">
            <dt className="text-sm text-zinc-500">Giao đến</dt>
            <dd className="font-medium">{shipping.name} · {shipping.phone}</dd>
            <dd>{shipping.address}</dd>
          </div>
        )}
      </dl>
      <section aria-labelledby="checkout-orders" className="space-y-3">
        <h2 id="checkout-orders" className="text-xl font-bold">Đơn hàng theo shop</h2>
        {orders.map((order) => {
          const allocation = allocations.get(order.id)
          return (
            <article key={order.id} className="space-y-3 rounded-2xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
              <h3 className="font-bold wrap-anywhere">{order.shop.name}</h3>
              <p className="break-all text-sm text-zinc-500">Mã đơn {order.id}</p>
              <Link to={`/orders/${order.id}`} className={buyerLink}>Xem chi tiết đơn</Link>
              <ul className="space-y-2 border-t border-zinc-200 pt-3 text-sm dark:border-zinc-800">
                {order.items.map((item) => (
                  <li key={item.id} className="flex flex-wrap justify-between gap-x-4 gap-y-1">
                    <span className="min-w-0 wrap-anywhere">{item.product_name} × {item.quantity}</span>
                    <span className="min-w-0 wrap-anywhere">{productPrice.format(item.line_total)}</span>
                  </li>
                ))}
              </ul>
              <p className="flex flex-wrap justify-between gap-x-4 gap-y-1 text-sm font-semibold">
                <span>{allocation ? (allocation.status === 'refunded' ? 'Đã hoàn cho đơn này' : 'Thanh toán cho đơn này') : 'Tổng đơn'}</span>
                <span>{productPrice.format(allocation?.amount ?? order.total_amount)}</span>
              </p>
            </article>
          )
        })}
      </section>
    </div>
  )
}
