import { useEffect, useState } from 'react'
import { Link, useLocation, useParams } from 'react-router-dom'
import { ApiError, api, type SellerOrder } from '../../shared/api/client'
import { Alert, Button, Spinner } from '../../shared/auth/components/ui'
import { describeError } from '../../shared/auth/errors'
import { AppShell } from '../../shared/layout/AppShell'
import { OrderBadge, orderDate, orderSecondary } from '../../shared/orders/orderUi'
import { OrderDetails } from '../../shared/orders/OrderDetails'

const detailPanel = 'min-w-0 rounded-lg border border-slate-200 bg-white p-4 shadow-xs sm:p-5'

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
    api.order(id).then(
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
      <h1 className="text-[22px] leading-7 font-semibold tracking-tight">Đơn #{id.slice(0, 8).toUpperCase()}</h1>
      {notice && <Alert tone="success">{notice}</Alert>}
      {actionError && <Alert>{actionError}</Alert>}
      {loading ? <div className={detailPanel}><Spinner label="Đang tải chi tiết…" /></div> : error ? (
        <div className="space-y-3">
          <Alert>{error}</Alert>
          <button type="button" className={orderSecondary} onClick={reload}>Thử lại</button>
        </div>
      ) : order && (
        <>
          <section className={`${detailPanel} space-y-4`} aria-label="Trạng thái và thao tác giao hàng">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="space-y-1">
                <OrderBadge status={order.status} indicator />
                <p className="text-[13px] text-slate-500">Ngày đặt <time dateTime={order.created_at}>{orderDate.format(new Date(order.created_at))}</time></p>
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
              <div className="space-y-3 rounded-md border border-slate-200 bg-slate-50 p-3">
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
          <OrderDetails order={order} panelClassName={detailPanel} />
        </>
      )}
    </>
  )
}

export default function SellerOrderDetailPage() {
  const { orderId } = useParams()
  const { search, state } = useLocation()

  return (
    <AppShell>
      <Link className="inline-flex min-h-11 items-center rounded-md text-sm font-semibold text-brand-700 hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-500" to={`/seller/orders${search}`} state={state}>
        <span aria-hidden="true" className="mr-2">←</span>Về danh sách đơn hàng
      </Link>
      {orderId && <SellerOrderDetail key={orderId} id={orderId} />}
    </AppShell>
  )
}
