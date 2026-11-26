import type { ReactNode } from 'react'
import { Alert, Spinner } from '../shared/auth/components/ui'

export const buyerLink = 'inline-flex min-h-11 max-w-full items-center rounded-lg px-3 py-2 text-sm font-semibold text-brand-700 hover:bg-brand-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-500 dark:text-brand-100 dark:hover:bg-brand-900/40'

export function BuyerRequestError({ message, retry }: { message: string; retry?: () => void }) {
  return (
    <div className="min-w-0 space-y-2">
      <Alert>{message}</Alert>
      {retry && <button type="button" onClick={retry} className={buyerLink}>Thử lại</button>}
    </div>
  )
}

export function BuyerLoading({ label }: { label: string }) {
  return (
    <div className="grid min-h-28 place-items-center rounded-2xl border border-zinc-200 bg-white p-5 text-center dark:border-zinc-800 dark:bg-zinc-900">
      <Spinner label={label} />
    </div>
  )
}

export function BuyerEmptyState({ title, description, children }: {
  title: string
  description?: string
  children?: ReactNode
}) {
  return (
    <section className="space-y-2 rounded-2xl border border-dashed border-zinc-300 p-6 text-center sm:py-10 dark:border-zinc-700">
      <h2 className="text-lg font-semibold">{title}</h2>
      {description && <p className="text-sm text-zinc-600 dark:text-zinc-400">{description}</p>}
      {children && <div className="mt-3 flex flex-wrap justify-center gap-2">{children}</div>}
    </section>
  )
}
