import type { Order } from '../api/client'
import { orderDate, orderMoney, orderPanel } from './orderUi'

export function OrderDetails({ order, panelClassName = orderPanel }: { order: Order; panelClassName?: string }) {
  const milestones = [
    { label: 'Đặt đơn', at: order.created_at },
    { label: 'Thanh toán', at: order.paid_at },
    { label: 'Bàn giao để vận chuyển', at: order.shipped_at },
    { label: 'Hoàn tất giao hàng', at: order.completed_at },
    { label: 'Hủy đơn', at: order.cancelled_at },
  ]

  return (
    <div className="grid items-start gap-4 lg:grid-cols-[minmax(0,1.35fr)_minmax(0,1fr)]">
      <section className={panelClassName} aria-labelledby="order-items">
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
        <section className={panelClassName} aria-labelledby="order-recipient">
          <h2 id="order-recipient" className="text-lg font-semibold">Thông tin nhận hàng</h2>
          <dl className="mt-3 space-y-3 text-sm wrap-anywhere">
            <div><dt className="text-zinc-600 dark:text-zinc-400">Người nhận</dt><dd className="mt-0.5 font-medium">{order.shipping.name}</dd></div>
            <div><dt className="text-zinc-600 dark:text-zinc-400">Số điện thoại</dt><dd className="mt-0.5 font-medium">{order.shipping.phone}</dd></div>
            <div><dt className="text-zinc-600 dark:text-zinc-400">Địa chỉ</dt><dd className="mt-0.5 font-medium whitespace-pre-wrap">{order.shipping.address}</dd></div>
          </dl>
        </section>
        <section className={panelClassName} aria-labelledby="order-timeline">
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
