import type { ReactNode } from 'react'

export const BRAND = 'E-Market'

export function Logo({ light = false, variant = 'default' }: { light?: boolean; variant?: 'default' | 'auth' }) {
  return (
    <div className={`flex w-fit max-w-full shrink-0 items-center rounded-lg ${light ? 'bg-white' : ''}`}>
      <img
        src="/logo.png"
        alt={BRAND}
        width={2172}
        height={724}
        className={variant === 'auth'
          ? 'block h-auto w-48 max-w-full sm:w-56'
          : 'block h-auto w-40 max-w-full rounded-lg dark:bg-white'}
      />
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

const loginPerks = [
  'Gợi ý sản phẩm hợp ngân sách của bạn.',
  'Một giỏ hàng, nhiều shop – tự tách đơn.',
  'Theo dõi đơn hàng từng bước.',
]

/** Editorial two-column layout used only on the login page. */
export function LoginLayout({ title, subtitle, children, footer }: { title: string; subtitle: string; children: ReactNode; footer: ReactNode }) {
  return (
    <div className="login-page grid min-h-screen w-full grid-cols-1 text-[#18181B] lg:grid-cols-[52fr_48fr]">
      <aside className="hidden flex-col justify-between gap-6 border-r border-[#EFECE6] bg-[#F7F5F2] px-8 py-6 lg:flex xl:px-20 xl:py-[clamp(2rem,4vh,4rem)]">
        <div className="mx-auto w-4/5 max-w-[538px]">
          <Logo variant="auth" />
        </div>

        <div className="mx-auto w-4/5 max-w-[538px] py-2">
          <img
            src="/login-marketplace.png"
            alt="Tai nghe, giày sneaker, túi xách và phụ kiện trên nền đá sáng"
            width={1200}
            height={896}
            className="mb-6 block h-auto w-full rounded-xl border border-stone-200/70 shadow-[0_16px_32px_-12px_rgba(24,24,27,0.08)]"
          />
          <h2 className="mb-3 text-[21px] font-semibold leading-tight tracking-tight text-[#18181B] xl:text-[22px]">
            Mua sắm thông minh, đúng thứ bạn cần.
          </h2>
          <p className="mb-8 max-w-[416px] text-[13px] leading-[1.8] text-[#52525B]">
            Khám phá sản phẩm phù hợp với phong cách và ngân sách của bạn.
          </p>
          <ul className="space-y-4">
            {loginPerks.map((perk, index) => (
              <li key={perk} className="flex items-center gap-3 text-xs font-medium tracking-tight text-stone-800">
                <span className="grid size-5 shrink-0 place-items-center rounded-full border border-stone-300 font-mono text-[10px] font-medium tracking-wide text-stone-400">
                  0{index + 1}
                </span>
                <span>{perk}</span>
              </li>
            ))}
          </ul>
        </div>

        <p className="text-xs tracking-wide text-stone-400">
          © {new Date().getFullYear()} {BRAND}. Dự án học phần SOA.
        </p>
      </aside>

      <main className="flex min-h-screen items-center justify-center bg-white px-6 py-8 sm:px-10 xl:px-12">
        <div className="w-full max-w-[420px] @container">
          <div className="mb-7 lg:hidden"><Logo variant="auth" /></div>
          <header>
            <h1 className="text-[26px] font-semibold leading-tight tracking-tight text-[#18181B] sm:text-[32px]">{title}</h1>
            <p className="mt-1.5 text-[13px] leading-relaxed text-[#71717A]">{subtitle}</p>
          </header>
          <div className="mt-7">
            {children}
          </div>
          <p className="mt-8 text-center text-[13px] tracking-tight text-[#71717A]">{footer}</p>
        </div>
      </main>
    </div>
  )
}
