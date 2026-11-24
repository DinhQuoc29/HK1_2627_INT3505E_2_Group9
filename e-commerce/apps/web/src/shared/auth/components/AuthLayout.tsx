import type { ReactNode } from 'react'

export const BRAND = 'E-Market'

export function Logo({ light = false }: { light?: boolean }) {
  return (
    <div className="flex items-center gap-2.5">
      <span className={`grid size-9 place-items-center rounded-xl ${light ? 'bg-white/15 ring-1 ring-white/30' : 'bg-brand-600'}`}>
        <svg className="size-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
          <path d="M5 8h14l-1.3 10a2 2 0 0 1-2 1.7H8.3a2 2 0 0 1-2-1.7L5 8Zm3.5-1.5a3.5 3.5 0 0 1 7 0" />
        </svg>
      </span>
      <span className={`text-lg font-bold tracking-tight ${light ? 'text-white' : 'text-zinc-900 dark:text-white'}`}>{BRAND}</span>
    </div>
  )
}

const perks = [
  'Gợi ý sản phẩm hợp ngân sách của bạn',
  'Một giỏ hàng, nhiều shop – tự tách đơn',
  'Theo dõi đơn hàng từng bước',
]

function ProductCard({ tone, price, label, className }: { tone: string; price: string; label: string; className?: string }) {
  return (
    <div className={`w-44 rounded-2xl bg-white p-3 text-zinc-900 shadow-xl shadow-black/15 ${className ?? ''}`} aria-hidden>
      <div className={`h-24 rounded-xl ${tone}`} />
      <p className="mt-2.5 text-xs font-medium text-zinc-500">{label}</p>
      <p className="text-sm font-bold text-brand-600">{price}</p>
    </div>
  )
}

function BrandPanel() {
  return (
    <aside className="relative hidden overflow-hidden bg-gradient-to-br from-brand-500 via-brand-600 to-brand-900 p-12 text-white lg:flex lg:flex-col lg:justify-between">
      <div className="pointer-events-none absolute -right-24 -top-24 size-96 rounded-full bg-white/10 blur-2xl" aria-hidden />
      <div className="pointer-events-none absolute -bottom-32 -left-16 size-96 rounded-full bg-black/10 blur-2xl" aria-hidden />
      <Logo light />
      <div className="relative">
        <div className="relative mb-12 h-56" aria-hidden>
          <ProductCard tone="bg-gradient-to-br from-amber-200 to-orange-300" label="Tai nghe không dây" price="590.000₫" className="absolute left-0 top-6 -rotate-6" />
          <ProductCard tone="bg-gradient-to-br from-sky-200 to-indigo-300" label="Bình giữ nhiệt 500ml" price="189.000₫" className="absolute left-36 top-0 rotate-3" />
          <span className="absolute left-60 top-40 rounded-full bg-white px-3 py-1.5 text-xs font-semibold text-brand-700 shadow-lg">✦ Gợi ý cho bạn</span>
        </div>
        <h2 className="max-w-md text-3xl font-bold leading-tight tracking-tight">Mua sắm thông minh, đúng thứ bạn cần.</h2>
        <ul className="mt-6 space-y-3 text-sm text-white/90">
          {perks.map((p) => (
            <li key={p} className="flex items-center gap-2.5">
              <svg className="size-5 shrink-0 text-white" viewBox="0 0 20 20" fill="currentColor" aria-hidden>
                <path fillRule="evenodd" d="M10 18a8 8 0 1 0 0-16 8 8 0 0 0 0 16Zm3.7-9.3a1 1 0 0 0-1.4-1.4L9 10.6 7.7 9.3a1 1 0 0 0-1.4 1.4l2 2a1 1 0 0 0 1.4 0l4-4Z" clipRule="evenodd" />
              </svg>
              {p}
            </li>
          ))}
        </ul>
      </div>
      <p className="relative text-xs text-white/60">© {new Date().getFullYear()} {BRAND}. Dự án học phần SOA.</p>
    </aside>
  )
}

export function AuthLayout({ title, subtitle, children, footer }: { title: string; subtitle: string; children: ReactNode; footer: ReactNode }) {
  return (
    <div className="grid min-h-full lg:grid-cols-[1.05fr_1fr]">
      <BrandPanel />
      <main className="flex items-center justify-center px-5 py-10 sm:px-8">
        <div className="w-full max-w-[400px]">
          <div className="mb-8 lg:hidden"><Logo /></div>
          <h1 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-white">{title}</h1>
          <p className="mt-1.5 text-sm text-zinc-500 dark:text-zinc-400">{subtitle}</p>
          <div className="mt-7 space-y-5">{children}</div>
          <p className="mt-8 text-center text-sm text-zinc-500 dark:text-zinc-400">{footer}</p>
        </div>
      </main>
    </div>
  )
}
