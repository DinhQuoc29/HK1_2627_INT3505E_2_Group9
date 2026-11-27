import type { ReactNode } from 'react'

const iconShapes = {
  bag: <><path d="M5 7h14l1 14H4L5 7Z" /><path d="M9 10V6a3 3 0 0 1 6 0v4" /></>,
  overview: <><rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" /><rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" /></>,
  products: <><rect x="3" y="5" width="18" height="15" rx="2" /><path d="M3 10h18m-11 4h4" /></>,
  orders: <><rect x="5" y="5" width="14" height="16" rx="2" /><path d="M9 5V3h6v2m-6 5h6m-6 4h6m-6 4h4" /></>,
  account: <><circle cx="12" cy="8" r="3" /><path d="M5 20v-1a5 5 0 0 1 5-5h4a5 5 0 0 1 5 5v1" /></>,
  logout: <path d="M10 4H5v16h5m4-12 4 4-4 4m4-4H9" />,
  verified: <><circle cx="12" cy="12" r="9" /><path d="m8.5 12 2.3 2.3 4.7-4.7" /></>,
  location: <><path d="M19 10c0 5-7 10-7 10s-7-5-7-10a7 7 0 1 1 14 0Z" /><circle cx="12" cy="10" r="2.3" /></>,
  calendar: <><rect x="4" y="5" width="16" height="15" rx="2" /><path d="M8 3v4m8-4v4M4 10h16" /></>,
  edit: <><path d="m14.5 5.5 4 4M5 19l4.3-1 10-10a2 2 0 0 0-4-4l-10 10L5 19Z" /></>,
  chevron: <path d="m9 6 6 6-6 6" />,
  arrow: <path d="M4 12h15m-6-6 6 6-6 6" />,
  info: <><circle cx="12" cy="12" r="9" /><path d="M12 11v5m0-8h.01" /></>,
  add: <path d="M12 5v14m-7-7h14" />,
  search: <><circle cx="10.5" cy="10.5" r="6" /><path d="m15 15 5 5" /></>,
  sort: <path d="M4 6h16M4 12h11M4 18h6" />,
  lock: <><rect x="5" y="10" width="14" height="11" rx="2" /><path d="M8 10V7a4 4 0 1 1 8 0v3m-4 4v3" /></>,
  storefront: <><path d="M4 10v10h16V10M3 10l2-6h14l2 6M3 10a3 3 0 0 0 6 0 3 3 0 0 0 6 0 3 3 0 0 0 6 0M10 20v-5h4v5M9 10l1-6m5 6-1-6" /></>,
} satisfies Record<string, ReactNode>

type SellerIconName = keyof typeof iconShapes

export function SellerIcon({ name, className = 'size-[18px]' }: { name: SellerIconName; className?: string }) {
  return (
    <svg
      aria-hidden="true"
      className={`shrink-0 ${className}`}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.7}
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      {iconShapes[name]}
    </svg>
  )
}

export function SellerInitials({ name }: { name: string }) {
  const words = name.trim().split(/\s+/).filter(Boolean)
  return <>{words.slice(-2).map((word) => Array.from(word)[0]).join('').toLocaleUpperCase('vi-VN') || 'EM'}</>
}

export const sellerCard = 'min-w-0 rounded-xl border border-slate-200/80 bg-white p-4 shadow-[0_1px_3px_rgba(0,0,0,0.04)] sm:p-5 dark:border-slate-800 dark:bg-slate-900'
export const sellerAccountPanel = 'min-w-0 rounded-lg border border-slate-200 bg-white p-4 shadow-xs sm:p-5'
export const sellerTextLink = 'inline-flex min-h-8 items-center gap-1 rounded text-[13px] font-semibold text-(--seller-accent) hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-(--seller-accent) dark:text-brand-100'
