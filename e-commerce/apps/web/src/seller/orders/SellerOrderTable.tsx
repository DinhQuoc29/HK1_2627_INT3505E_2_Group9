import { Link } from 'react-router-dom'
import type { SellerOrder } from '../../shared/api/client'
import { OrderBadge, orderDate, orderMoney } from '../../shared/orders/orderUi'
import { SellerIcon } from '../sellerUi'

const number = new Intl.NumberFormat('vi-VN')
const cell = 'min-w-0 @min-[48rem]:table-cell @min-[48rem]:px-4 @min-[48rem]:py-3.5 @min-[48rem]:align-middle'
const mobileLabel = 'mb-0.5 block text-[11px] font-medium text-slate-500 @min-[48rem]:hidden'
const focus = 'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-(--seller-accent)'
const columns = ['Mã đơn hàng', 'Ngày đặt hàng', 'Số sản phẩm', 'Tổng tiền', 'Trạng thái', 'Thao tác']

function OrderRow({ order, statusSearch, query }: { order: SellerOrder; statusSearch: string; query: string }) {
  const code = order.id.slice(0, 8).toUpperCase()
  const detail = `/seller/orders/${encodeURIComponent(order.id)}${statusSearch}`
  const state = query ? { orderQuery: query } : undefined
  const quantity = order.items.reduce((total, item) => total + item.quantity, 0)
  const action = order.status === 'paid' ? 'Chuẩn bị hàng' : 'Xem chi tiết'
  const refund = (order.refunded_amount ?? 0) > 0

  return (
    <tr role="row" className="grid grid-cols-2 gap-x-3 gap-y-3 p-3.5 text-[13px] text-slate-700 transition-colors hover:bg-slate-50/70 @min-[48rem]:table-row">
      <th scope="row" role="rowheader" className={`${cell} col-start-1 row-start-1 text-left font-medium`}>
        <Link to={detail} state={state} className={`inline-block rounded font-mono text-xs font-semibold text-slate-900 hover:text-(--seller-accent) hover:underline ${focus}`}>#{code}</Link>
        <p className="mt-0.5 text-xs font-normal text-slate-500 wrap-anywhere">{order.shipping.name}</p>
      </th>
      <td role="cell" className={`${cell} col-start-1 row-start-2`}>
        <span className={mobileLabel}>Ngày đặt hàng</span>
        <time dateTime={order.created_at} className="tabular-nums">{orderDate.format(new Date(order.created_at))}</time>
      </td>
      <td role="cell" className={`${cell} col-start-2 row-start-2`}>
        <span className={mobileLabel}>Số sản phẩm</span>
        <span className="tabular-nums">{number.format(quantity)} sản phẩm</span>
      </td>
      <td role="cell" className={`${cell} col-start-1 row-start-3`}>
        <span className={mobileLabel}>Tổng tiền</span>
        <span className="font-semibold text-slate-900 tabular-nums wrap-anywhere">{orderMoney.format(order.total_amount)}</span>
        {refund ? (
          <span className="mt-0.5 block text-[11px] text-slate-600">Đã hoàn tiền</span>
        ) : order.paid_at && (
          <span className="mt-0.5 block text-[11px] text-emerald-700">Đã thanh toán</span>
        )}
      </td>
      <td role="cell" className={`${cell} col-start-2 row-start-1 justify-self-end self-start`}>
        <OrderBadge status={order.status} indicator />
      </td>
      <td role="cell" className={`${cell} col-start-2 row-start-3 justify-self-end self-end text-right`}>
        <Link
          to={detail}
          state={state}
          aria-label={`${action} cho đơn #${code}`}
          className={`inline-flex min-h-9 items-center justify-center gap-1 rounded-md px-2.5 text-xs font-medium leading-tight transition-colors ${focus} ${
            order.status === 'paid'
              ? 'bg-(--seller-accent) text-white hover:bg-[#D94325]'
              : 'border border-slate-200 bg-white text-slate-700 hover:border-slate-300 hover:bg-slate-50'
          }`}
        >
          {action}
          {order.status !== 'paid' && <SellerIcon name="arrow" className="size-3.5" />}
        </Link>
      </td>
    </tr>
  )
}

export function SellerOrderTable({ orders, statusSearch, query }: { orders: SellerOrder[]; statusSearch: string; query: string }) {
  return (
    <table aria-label="Danh sách đơn hàng" role="table" className="block w-full text-left @min-[48rem]:table @min-[48rem]:table-fixed">
      <colgroup className="hidden @min-[48rem]:table-column-group">
        <col />
        <col className="w-[20%]" />
        <col className="w-[13%]" />
        <col className="w-[14%]" />
        <col className="w-40" />
        <col className="w-36" />
      </colgroup>
      <thead role="rowgroup" className="hidden @min-[48rem]:table-header-group">
        <tr role="row" className="border-b border-slate-200 bg-slate-50/80 text-xs font-semibold tracking-wide text-slate-500 uppercase">
          {columns.map((column) => <th key={column} scope="col" role="columnheader" className="px-4 py-3.5 last:text-right">{column}</th>)}
        </tr>
      </thead>
      <tbody role="rowgroup" className="block divide-y divide-slate-100 @min-[48rem]:table-row-group">
        {orders.map((order) => <OrderRow key={order.id} order={order} statusSearch={statusSearch} query={query} />)}
      </tbody>
    </table>
  )
}
