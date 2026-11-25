import { useCallback } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, type CheckoutResult } from '../../shared/api/client'
import { Alert, Spinner } from '../../shared/auth/components/ui'
import { BuyerStoreLayout } from '../BuyerStoreLayout'
import { CatalogError, catalogLink, productPrice } from '../catalog/catalogUi'
import { catalogErrorMessage, useCatalogRequest } from '../catalog/useCatalogRequest'

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
        <Link to="/products" className={`inline-block ${catalogLink}`}>Tiếp tục mua sắm</Link>
      </div>
    </BuyerStoreLayout>
  )
}

function ReceiptLoader({ id }: { id: string }) {
  const load = useCallback(() => api.checkoutResult(id), [id])
  const { state, retry } = useCatalogRequest(load)
  if (state.status === 'loading') return <Spinner label="Đang tải kết quả thanh toán…" />
  if (state.status === 'error') {
    return <CatalogError message={catalogErrorMessage(state.error, 'Không tải được kết quả thanh toán.')} retry={retry} />
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
      <dl className="grid gap-4 rounded-2xl border border-zinc-200 bg-white p-5 sm:grid-cols-2 dark:border-zinc-800 dark:bg-zinc-900">
        <div><dt className="text-sm text-zinc-500">Mã lượt mua</dt><dd className="break-all font-medium">{result.id}</dd></div>
        <div><dt className="text-sm text-zinc-500">Mã thanh toán</dt><dd className="break-all font-medium">{payment.id}</dd></div>
        <div><dt className="text-sm text-zinc-500">Tổng đơn hàng</dt><dd className="font-bold">{productPrice.format(result.total_amount)}</dd></div>
        {payment.status === 'succeeded' && (
          <div><dt className="text-sm text-zinc-500">Đã thanh toán mô phỏng</dt><dd className="font-bold">{productPrice.format(payment.amount)}</dd></div>
        )}
        {shipping && (
          <div className="sm:col-span-2">
            <dt className="text-sm text-zinc-500">Giao đến</dt>
            <dd className="break-words font-medium">{shipping.name} · {shipping.phone}</dd>
            <dd className="break-words">{shipping.address}</dd>
          </div>
        )}
      </dl>
      <section aria-labelledby="checkout-orders" className="space-y-3">
        <h2 id="checkout-orders" className="text-xl font-bold">Đơn hàng theo shop</h2>
        {orders.map((order) => {
          const allocation = allocations.get(order.id)
          return (
            <article key={order.id} className="space-y-3 rounded-2xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
              <h3 className="break-words font-bold">{order.shop.name}</h3>
              <p className="break-all text-sm text-zinc-500">Mã đơn {order.id}</p>
              <ul className="space-y-2 border-t border-zinc-200 pt-3 text-sm dark:border-zinc-800">
                {order.items.map((item) => (
                  <li key={item.id} className="flex flex-wrap justify-between gap-x-4 gap-y-1">
                    <span className="min-w-0 break-words">{item.product_name} × {item.quantity}</span>
                    <span>{productPrice.format(item.line_total)}</span>
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
