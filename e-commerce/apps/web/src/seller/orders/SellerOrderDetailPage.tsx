import { useEffect, useState } from 'react'
import { Link, useLocation, useParams } from 'react-router-dom'
import { ApiError, api, type SellerOrder } from '../../shared/api/client'
import { Alert, Button, Spinner } from '../../shared/auth/components/ui'
import { describeError } from '../../shared/auth/errors'
import { AppShell } from '../../shared/layout/AppShell'
import { OrderBadge, orderDate, orderMoney, orderPanel, orderSecondary } from './orderUi'

function OrderDetails({ order }: { order: SellerOrder }) {
  const milestones = [
    { label: 'Đặt đơn', at: order.created_at },
    { label: 'Thanh toán', at: order.paid_at },
    { label: 'Bàn giao để vận chuyển', at: order.shipped_at },
    { label: 'Hoàn tất giao hàng', at: order.completed_at },
    { label: 'Hủy đơn', at: order.cancelled_at },
  ]

  return (
    <div className="grid items-start gap-4 lg:grid-cols-[minmax(0,1.35fr)_minmax(0,1fr)]">
      <section className={orderPanel} aria-labelledby="order-items">
        <h2 id="order-items" className="text-lg font-semibold">Sản phẩm trong đơn</h2>
        <ul className="mt-2 divide-y divide-zinc-200 dark:divide-zinc-800">
          {order.items.map((item) => (
            <li key={item.id} className="flex flex-wrap items-start justify-between gap-2 py-3 text-sm">
              <div className="min-w-0 flex-1 basis-36">
                <p className="font-medium wrap-anywhere">{item.product_name}</p>
                <p className="mt-0.5 text-zinc-600 dark:text-zinc-400">{item.quantity} × {orderMoney.format(item.unit_price)}</p>
              </div>
              <span className="font-semibold tabular-nums">{orderMoney.format(item.line_total)}</span>
            </li>
          ))}
        </ul>
        <div className="flex flex-wrap justify-between gap-2 border-t border-zinc-200 pt-3 text-sm dark:border-zinc-800">
          <span>Tổng tiền đơn hàng</span>
          <strong className="text-base tabular-nums">{orderMoney.format(order.total_amount)}</strong>
        </div>
      </section>
      <div className="min-w-0 space-y-4">
        <section className={orderPanel} aria-labelledby="order-recipient">
          <h2 id="order-recipient" className="text-lg font-semibold">Thông tin nhận hàng</h2>
          <dl className="mt-3 space-y-3 text-sm wrap-anywhere">
            <div><dt className="text-zinc-600 dark:text-zinc-400">Người nhận</dt><dd className="mt-0.5 font-medium">{order.shipping.name}</dd></div>
            <div><dt className="text-zinc-600 dark:text-zinc-400">Số điện thoại</dt><dd className="mt-0.5 font-medium">{order.shipping.phone}</dd></div>
            <div><dt className="text-zinc-600 dark:text-zinc-400">Địa chỉ</dt><dd className="mt-0.5 font-medium whitespace-pre-wrap">{order.shipping.address}</dd></div>
          </dl>
        </section>
        <section className={orderPanel} aria-labelledby="order-timeline">
          <h2 id="order-timeline" className="text-lg font-semibold">Tiến trình đơn hàng</h2>
          <ol className="mt-4 space-y-3 border-l border-zinc-200 pl-4 text-sm dark:border-zinc-700">
            {milestones.map(({ label, at }) => at && (
              <li key={label}>
                <p className="font-medium">{label}</p>
                <time className="text-zinc-600 dark:text-zinc-400" dateTime={at}>{orderDate.format(new Date(at))}</time>
              </li>
            ))}
          </ol>
        </section>
      </div>
    </div>
  )
}

function SellerOrderDetail({ id }: { id: string }) {
  const [order, setOrder] = useState<SellerOrder>()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string>()
  const [actionError, setActionError] = useState<string>()
  const [notice, setNotice] = useState<string>()
  const [retry, setRetry] = useState(0)
  const [confirming, setConfirming] = useState(false)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    let cancelled = false
    api.sellerOrder(id).then(
      (data) => { if (!cancelled) { setOrder(data); setLoading(false) } },
      (failure) => {
        if (cancelled) return
        setError(describeError(failure).message ?? 'Không tải được đơn hàng.')
        setLoading(false)
      },
    )
    return () => { cancelled = true }
  }, [id, retry])

  const reload = () => {
    setError(undefined)
    setLoading(true)
    setRetry((previous) => previous + 1)
  }

  const canShip = order?.status === 'paid'
  const canComplete = order?.status === 'shipping'
  const advance = async () => {
    setSaving(true)
    setActionError(undefined)
    setNotice(undefined)
    try {
      const updated = await (canShip ? api.shipSellerOrder(id) : api.completeSellerOrder(id))
      setOrder(updated)
      setNotice(canShip ? 'Đã chuyển đơn hàng sang Đang giao.' : 'Đã xác nhận giao hàng thành công.')
      setConfirming(false)
    } catch (failure) {
      if (failure instanceof ApiError && failure.status === 409) {
        setActionError('Trạng thái đơn đã thay đổi. Hãy kiểm tra thông tin mới nhất.')
        setConfirming(false)
        reload()
      } else {
        setActionError(describeError(failure).message ?? 'Không cập nhật được trạng thái đơn hàng.')
      }
    } finally {
      setSaving(false)
    }
  }

  return (
    <>
      <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">Đơn #{id.slice(0, 8).toUpperCase()}</h1>
      {notice && <Alert tone="success">{notice}</Alert>}
      {actionError && <Alert>{actionError}</Alert>}
      {loading ? <div className={orderPanel}><Spinner label="Đang tải chi tiết…" /></div> : error ? (
        <div className="space-y-3">
          <Alert>{error}</Alert>
          <button type="button" className={orderSecondary} onClick={reload}>Thử lại</button>
        </div>
      ) : order && (
        <>
          <section className={`${orderPanel} space-y-4`} aria-label="Trạng thái và thao tác giao hàng">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="space-y-1">
                <OrderBadge status={order.status} />
                <p className="text-sm text-zinc-600 dark:text-zinc-400">Ngày đặt <time dateTime={order.created_at}>{orderDate.format(new Date(order.created_at))}</time></p>
              </div>
              {(canShip || canComplete) && !confirming && (
                <div className="w-fit">
                  <Button onClick={() => { setActionError(undefined); setConfirming(true) }}>
                    {canShip ? 'Xác nhận đã bàn giao' : 'Xác nhận đã giao'}
                  </Button>
                </div>
              )}
            </div>
            {(canShip || canComplete) && confirming && (
              <div className="space-y-3 rounded-xl bg-zinc-50 p-3 dark:bg-zinc-800">
                <p className="text-sm">{canShip
                  ? 'Chỉ xác nhận sau khi bạn đã bàn giao đơn cho đơn vị vận chuyển.'
                  : 'Chỉ xác nhận sau khi đơn đã được giao đến người nhận.'}</p>
                <div className="flex flex-wrap gap-2">
                  <div className="w-fit"><Button loading={saving} onClick={advance}>{canShip ? 'Chuyển sang Đang giao' : 'Hoàn tất giao hàng'}</Button></div>
                  <button type="button" className={orderSecondary} disabled={saving} onClick={() => { setActionError(undefined); setConfirming(false) }}>Hủy thao tác</button>
                </div>
              </div>
            )}
          </section>
          <OrderDetails order={order} />
        </>
      )}
    </>
  )
}

export default function SellerOrderDetailPage() {
  const { orderId } = useParams()
  const { search } = useLocation()

  return (
    <AppShell>
      <Link className="inline-flex min-h-11 items-center rounded-md text-sm font-semibold text-brand-700 hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-500 dark:text-brand-100" to={`/seller/orders${search}`}>
        <span aria-hidden="true" className="mr-2">←</span>Về danh sách đơn hàng
      </Link>
      {orderId && <SellerOrderDetail key={orderId} id={orderId} />}
    </AppShell>
  )
}
