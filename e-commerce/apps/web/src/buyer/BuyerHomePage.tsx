import { Link } from 'react-router-dom'
import { api } from '../shared/api/client'
import { useAuth } from '../shared/auth/AuthContext'
import { BuyerStoreLayout } from '../shared/layout/BuyerStoreLayout'
import { BuyerEmptyState, BuyerLoading, BuyerRequestError } from './BuyerFeedback'
import { useBuyerRequest } from './useBuyerRequest'

const benefits = [
  { icon: '◎', title: 'Nhiều lựa chọn', description: 'Khám phá sản phẩm từ nhiều shop trong cùng một nơi.' },
  { icon: '₫', title: 'Chọn theo ngân sách', description: 'Tìm món phù hợp với mức giá bạn đang cân nhắc.' },
  { icon: '↗', title: 'Theo dõi đơn hàng', description: 'Xem tiến trình của từng shop sau khi đặt mua.' },
]

export default function BuyerHomePage() {
  const { status } = useAuth()
  return (
    <BuyerStoreLayout>
      <div className="mx-auto max-w-7xl space-y-12 px-4 py-7 sm:px-6 sm:py-10 lg:space-y-16">
        <section className="relative isolate overflow-hidden rounded-[2rem] bg-gradient-to-br from-orange-50 via-rose-50 to-amber-100 px-5 py-8 dark:from-zinc-900 dark:via-zinc-900 dark:to-brand-900/50 sm:px-10 sm:py-14 lg:grid lg:min-h-[25rem] lg:grid-cols-[1.1fr_0.9fr] lg:items-center lg:px-14">
          <div className="pointer-events-none absolute -right-28 -top-32 -z-10 size-[28rem] rounded-full bg-white/70 blur-3xl dark:bg-brand-500/10" aria-hidden />
          <div className="pointer-events-none absolute -bottom-40 left-1/3 -z-10 size-80 rounded-full bg-brand-300/30 blur-3xl" aria-hidden />
          <div className="relative z-10 max-w-2xl">
            <p className="inline-flex items-center gap-2 rounded-full border border-brand-200 bg-white/80 px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.14em] text-brand-700 dark:border-brand-800 dark:bg-zinc-950/50 dark:text-brand-100">
              <span className="size-1.5 rounded-full bg-brand-500" aria-hidden />
              Chào mừng đến E-Market
            </p>
            <h1 className="mt-4 text-3xl font-bold leading-[1.08] tracking-tight text-zinc-950 sm:mt-5 sm:text-5xl lg:text-[3.5rem] dark:text-white">
              Món bạn cần,<br />dễ tìm hơn mỗi ngày.
            </h1>
            <p className="mt-5 max-w-xl text-base leading-7 text-zinc-600 dark:text-zinc-300 sm:text-lg">
              Khám phá sản phẩm từ nhiều shop, tìm lựa chọn hợp ngân sách và quản lý đơn hàng thuận tiện.
            </p>
            <div className="mt-7 flex flex-wrap gap-3">
              <Link to="/products" className="inline-flex min-h-12 items-center justify-center gap-2 rounded-xl bg-brand-600 px-5 font-semibold text-white shadow-lg shadow-brand-600/20 transition hover:-translate-y-0.5 hover:bg-brand-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-600">
                Khám phá sản phẩm
                <span aria-hidden>→</span>
              </Link>
              {status === 'anonymous' && (
                <Link to="/register" className="inline-flex min-h-12 items-center justify-center rounded-xl border border-zinc-300 bg-white/70 px-5 font-semibold text-zinc-800 transition hover:bg-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-600 dark:border-zinc-700 dark:bg-zinc-950/40 dark:text-white dark:hover:bg-zinc-900">
                  Tạo tài khoản
                </Link>
              )}
            </div>
            <div className="mt-8 flex flex-wrap gap-x-5 gap-y-2 text-xs font-medium text-zinc-600 dark:text-zinc-300 sm:text-sm">
              <span className="inline-flex items-center gap-2"><span className="text-brand-600" aria-hidden>✓</span> Giỏ hàng nhiều shop</span>
              <span className="inline-flex items-center gap-2"><span className="text-brand-600" aria-hidden>✓</span> Thanh toán mô phỏng an toàn</span>
            </div>
          </div>

          <div className="relative mx-auto mt-10 hidden h-64 w-full max-w-md sm:block lg:mt-0" aria-hidden>
            <div className="absolute left-1/2 top-1/2 grid size-52 -translate-x-1/2 -translate-y-1/2 place-items-center rounded-full bg-gradient-to-br from-brand-500 to-brand-700 shadow-2xl shadow-brand-700/25 sm:size-60">
              <div className="grid size-36 place-items-center rounded-[2rem] border border-white/30 bg-white/15 text-7xl text-white shadow-inner sm:size-40">
                <svg viewBox="0 0 80 80" className="size-24 sm:size-28" fill="none" aria-hidden>
                  <path d="M14 29h52l-5 37H19l-5-37Z" fill="currentColor" fillOpacity=".96" />
                  <path d="M27 31v-7a13 13 0 0 1 26 0v7" stroke="white" strokeWidth="4" strokeLinecap="round" />
                  <path d="M28 44h24" stroke="#E8472B" strokeWidth="4" strokeLinecap="round" />
                </svg>
              </div>
            </div>
            <div className="absolute left-0 top-7 rounded-2xl border border-white/80 bg-white/90 p-4 shadow-xl shadow-orange-900/10 backdrop-blur dark:border-zinc-700 dark:bg-zinc-900/90">
              <span className="grid size-10 place-items-center rounded-xl bg-sky-100 text-lg text-sky-700 dark:bg-sky-950 dark:text-sky-300" aria-hidden>⌁</span>
              <p className="mt-3 text-xs font-medium text-zinc-500">Khám phá mỗi ngày</p>
              <p className="text-sm font-bold text-zinc-900 dark:text-white">Nhiều lựa chọn</p>
            </div>
            <div className="absolute bottom-5 right-0 rounded-2xl border border-white/80 bg-white/90 p-4 shadow-xl shadow-orange-900/10 backdrop-blur dark:border-zinc-700 dark:bg-zinc-900/90">
              <span className="grid size-10 place-items-center rounded-xl bg-emerald-100 text-lg text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300" aria-hidden>✓</span>
              <p className="mt-3 text-xs font-medium text-zinc-500">Mua sắm thuận tiện</p>
              <p className="text-sm font-bold text-zinc-900 dark:text-white">Từ nhiều shop</p>
            </div>
            <span className="absolute right-12 top-3 grid size-11 place-items-center rounded-full bg-amber-300 text-xl text-amber-900 shadow-lg" aria-hidden>✦</span>
            <span className="absolute bottom-4 left-12 grid size-9 place-items-center rounded-full bg-rose-200 text-rose-800 shadow-lg" aria-hidden>✧</span>
          </div>
        </section>

        <section aria-labelledby="buyer-categories">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <p className="text-sm font-semibold text-brand-600">Bắt đầu từ điều bạn thích</p>
              <h2 id="buyer-categories" className="mt-1 text-2xl font-bold tracking-tight text-zinc-900 dark:text-white">Khám phá danh mục</h2>
            </div>
            <Link to="/products" className="text-sm font-semibold text-brand-700 hover:underline dark:text-brand-100">Xem tất cả sản phẩm <span aria-hidden>→</span></Link>
          </div>
          <HomeCategories />
        </section>

        <section aria-labelledby="buyer-benefits" className="rounded-3xl border border-zinc-200 bg-white p-5 sm:p-8 dark:border-zinc-800 dark:bg-zinc-900">
          <div className="max-w-2xl">
            <p className="text-sm font-semibold text-brand-600">Mua sắm dễ dàng hơn</p>
            <h2 id="buyer-benefits" className="mt-1 text-2xl font-bold tracking-tight text-zinc-900 dark:text-white">Mọi thứ bạn cần, trong một trải nghiệm</h2>
          </div>
          <div className="mt-6 grid gap-5 md:grid-cols-3">
            {benefits.map((benefit) => (
              <article key={benefit.title} className="flex gap-4 rounded-2xl bg-zinc-50 p-4 dark:bg-zinc-950">
                <span className="grid size-11 shrink-0 place-items-center rounded-xl bg-brand-100 text-lg font-bold text-brand-700 dark:bg-brand-900/50 dark:text-brand-100" aria-hidden>{benefit.icon}</span>
                <div>
                  <h3 className="font-semibold text-zinc-900 dark:text-white">{benefit.title}</h3>
                  <p className="mt-1 text-sm leading-6 text-zinc-600 dark:text-zinc-400">{benefit.description}</p>
                </div>
              </article>
            ))}
          </div>
        </section>
      </div>
    </BuyerStoreLayout>
  )
}

function HomeCategories() {
  const { state, retry } = useBuyerRequest(api.catalogCategories)

  return (
    <div className="mt-5">
      {state.status === 'loading' && <BuyerLoading label="Đang tải danh mục…" />}
      {state.status === 'error' && <BuyerRequestError message="Không tải được danh mục." retry={retry} />}
      {state.status === 'ready' && (
        state.data.length ? (
          <ul className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            {state.data.map((category) => (
              <li key={category.slug}>
                <Link
                  to={`/products?${new URLSearchParams({ category: category.slug })}`}
                  className="group flex h-full min-h-20 items-center justify-between gap-2 rounded-2xl border border-zinc-200 bg-white p-4 font-semibold transition hover:border-brand-500 hover:shadow-md focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-500 dark:border-zinc-800 dark:bg-zinc-900"
                >
                  <span className="min-w-0 break-words">{category.name}</span>
                  <span className="shrink-0 text-zinc-400 group-hover:text-brand-600" aria-hidden>→</span>
                </Link>
              </li>
            ))}
          </ul>
        ) : <BuyerEmptyState title="Chưa có danh mục sản phẩm" />
      )}
    </div>
  )
}
