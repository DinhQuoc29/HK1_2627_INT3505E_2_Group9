import type { OrderStatus } from '../api/client'

const statuses: Record<OrderStatus, { label: string; style: string }> = {
  pending_payment: { label: 'Chờ thanh toán', style: 'bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300' },
  paid: { label: 'Chờ giao', style: 'bg-amber-50 text-amber-900 dark:bg-amber-950 dark:text-amber-200' },
  shipping: { label: 'Đang giao', style: 'bg-blue-50 text-blue-800 dark:bg-blue-950 dark:text-blue-200' },
  completed: { label: 'Đã giao', style: 'bg-emerald-50 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-200' },
  cancelled: { label: 'Đã hủy', style: 'bg-red-50 text-red-800 dark:bg-red-950 dark:text-red-200' },
}

export const orderStatusOptions = (Object.keys(statuses) as OrderStatus[]).map((key) => [key, statuses[key]] as const)
export const orderPanel = 'min-w-0 rounded-2xl border border-zinc-200 bg-white p-4 shadow-sm sm:p-5 dark:border-zinc-800 dark:bg-zinc-900'
export const orderSecondary = 'inline-flex min-h-11 items-center justify-center rounded-xl border border-zinc-300 px-4 py-2 text-sm font-semibold hover:bg-zinc-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-500 disabled:cursor-not-allowed disabled:opacity-50 dark:border-zinc-700 dark:hover:bg-zinc-800'
export const orderMoney = new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' })
export const orderDate = new Intl.DateTimeFormat('vi-VN', { dateStyle: 'medium', timeStyle: 'short', timeZone: 'Asia/Ho_Chi_Minh' })

export function OrderBadge({ status }: { status: OrderStatus }) {
  const { label, style } = statuses[status]
  return <span className={`inline-flex w-fit rounded-full px-2.5 py-1 text-xs font-semibold ${style}`}>{label}</span>
}
