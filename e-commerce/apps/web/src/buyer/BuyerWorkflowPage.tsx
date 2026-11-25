import { Link } from 'react-router-dom'
import { BuyerStoreLayout } from './BuyerStoreLayout'

type BuyerWorkflowPageProps = {
  title: string
  description: string
  icon: string
  nextStep: string
  actionHref?: string
  actionLabel?: string
}

export function BuyerWorkflowPage({
  title,
  description,
  icon,
  nextStep,
  actionHref = '/',
  actionLabel = 'Về trang chủ',
}: BuyerWorkflowPageProps) {
  return (
    <BuyerStoreLayout>
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 sm:py-12">
        <nav aria-label="Đường dẫn trang" className="mb-6 text-sm text-zinc-500">
          <Link to="/" className="hover:text-brand-700 dark:hover:text-brand-100">Trang chủ</Link>
          <span className="mx-2" aria-hidden>/</span>
          <span className="font-medium text-zinc-700 dark:text-zinc-200">{title}</span>
        </nav>

        <section className="mx-auto max-w-3xl rounded-3xl border border-zinc-200 bg-white px-6 py-10 text-center shadow-sm sm:px-10 sm:py-14 dark:border-zinc-800 dark:bg-zinc-900">
          <span className="mx-auto grid size-16 place-items-center rounded-2xl bg-brand-50 text-3xl text-brand-700 dark:bg-brand-900/40 dark:text-brand-100" aria-hidden>{icon}</span>
          <p className="mt-6 text-xs font-semibold uppercase tracking-[0.16em] text-brand-600">E-Market · Mua sắm</p>
          <h1 className="mt-2 text-2xl font-bold tracking-tight text-zinc-900 dark:text-white sm:text-3xl">{title}</h1>
          <p className="mx-auto mt-3 max-w-xl text-sm leading-6 text-zinc-600 dark:text-zinc-400 sm:text-base">{description}</p>

          <div className="mx-auto mt-8 max-w-xl rounded-2xl border border-dashed border-zinc-300 bg-zinc-50 px-5 py-5 text-left dark:border-zinc-700 dark:bg-zinc-950">
            <p className="text-sm font-semibold text-zinc-800 dark:text-zinc-100">Khung trang đã sẵn sàng</p>
            <p className="mt-1.5 text-sm leading-6 text-zinc-600 dark:text-zinc-400">
              {nextStep} Sản phẩm và dữ liệu mua hàng sẽ được nối vào các trang này ở những bước tiếp theo.
            </p>
          </div>

          <div className="mt-7 flex flex-wrap justify-center gap-3">
            <Link to={actionHref} className="inline-flex min-h-11 items-center justify-center rounded-xl bg-brand-600 px-4 font-semibold text-white transition hover:bg-brand-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-600">{actionLabel}</Link>
            {actionHref !== '/products' && <Link to="/products" className="inline-flex min-h-11 items-center justify-center rounded-xl border border-zinc-300 px-4 font-semibold text-zinc-700 transition hover:bg-zinc-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-600 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-800">Khám phá sản phẩm</Link>}
          </div>
        </section>
      </div>
    </BuyerStoreLayout>
  )
}
