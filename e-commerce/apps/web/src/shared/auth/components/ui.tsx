import { forwardRef, useId, useState, type InputHTMLAttributes, type ReactNode } from 'react'
import { passwordRules } from '../schemas'

const cx = (...c: (string | false | undefined)[]) => c.filter(Boolean).join(' ')

export function Spinner({ label }: { label?: string }) {
  return (
    <span role="status" className="inline-flex items-center gap-2 text-sm text-zinc-500">
      <svg className="size-4 animate-spin" viewBox="0 0 24 24" fill="none" aria-hidden>
        <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="3" opacity=".25" />
        <path d="M21 12a9 9 0 0 0-9-9" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
      </svg>
      {label && <span>{label}</span>}
    </span>
  )
}

export function Button({ loading, children, ...p }: { loading?: boolean } & React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      {...p}
      disabled={p.disabled || loading}
      className={cx(
        'inline-flex h-11 w-full items-center justify-center gap-2 rounded-xl bg-brand-600 px-4 text-sm font-semibold text-white shadow-sm shadow-brand-600/20',
        'transition hover:bg-brand-700 active:scale-[.99] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-600',
        'disabled:cursor-not-allowed disabled:opacity-60',
      )}
    >
      {loading && <Spinner />}
      {children}
    </button>
  )
}

export function Alert({ children, tone = 'error' }: { children: ReactNode; tone?: 'error' | 'info' | 'success' }) {
  return (
    <div
      role={tone === 'error' ? 'alert' : 'status'}
      className={cx(
        'flex gap-3 rounded-xl border px-4 py-3 text-sm',
        tone === 'error'
          ? 'border-red-200 bg-red-50 text-red-800 dark:border-red-900/60 dark:bg-red-950/40 dark:text-red-200'
          : tone === 'success'
            ? 'border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-900/60 dark:bg-emerald-950/40 dark:text-emerald-200'
            : 'border-zinc-200 bg-zinc-50 text-zinc-700 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-300',
      )}
    >
      <svg className="mt-0.5 size-4 shrink-0" viewBox="0 0 20 20" fill="currentColor" aria-hidden>
        <path fillRule="evenodd" d="M18 10a8 8 0 1 1-16 0 8 8 0 0 1 16 0Zm-8-5a.9.9 0 0 0-.9.9v4.2a.9.9 0 0 0 1.8 0V5.9A.9.9 0 0 0 10 5Zm0 8.2a1.1 1.1 0 1 0 0 2.2 1.1 1.1 0 0 0 0-2.2Z" clipRule="evenodd" />
      </svg>
      <div>{children}</div>
    </div>
  )
}

type FieldProps = { label: string; error?: string; hint?: string } & InputHTMLAttributes<HTMLInputElement>

const inputClass = (invalid: boolean) =>
  cx(
    'h-11 w-full rounded-xl border bg-white px-3.5 text-sm text-zinc-900 placeholder:text-zinc-400 transition dark:bg-zinc-900 dark:text-zinc-100',
    'focus:outline-none focus:ring-4',
    invalid
      ? 'border-red-400 focus:border-red-500 focus:ring-red-500/15'
      : 'border-zinc-300 hover:border-zinc-400 focus:border-brand-500 focus:ring-brand-500/15 dark:border-zinc-700 dark:hover:border-zinc-600',
  )

export const TextField = forwardRef<HTMLInputElement, FieldProps>(function TextField({ label, error, hint, className, ...p }, ref) {
  const id = useId()
  const describedBy = error ? `${id}-err` : hint ? `${id}-hint` : undefined
  return (
    <div className={className}>
      <label htmlFor={id} className="mb-1.5 block text-sm font-medium text-zinc-700 dark:text-zinc-300">{label}</label>
      <input id={id} ref={ref} aria-invalid={!!error} aria-describedby={describedBy} className={inputClass(!!error)} {...p} />
      {error ? (
        <p id={`${id}-err`} className="mt-1.5 text-xs text-red-600 dark:text-red-400">{error}</p>
      ) : hint ? (
        <p id={`${id}-hint`} className="mt-1.5 text-xs text-zinc-500">{hint}</p>
      ) : null}
    </div>
  )
})

type PasswordProps = FieldProps & { showRules?: boolean; value?: string }

export const PasswordField = forwardRef<HTMLInputElement, PasswordProps>(function PasswordField(
  { label, error, hint, showRules, value = '', className, ...p },
  ref,
) {
  const id = useId()
  const [visible, setVisible] = useState(false)
  const describedBy = error ? `${id}-err` : showRules ? `${id}-rules` : hint ? `${id}-hint` : undefined
  return (
    <div className={className}>
      <label htmlFor={id} className="mb-1.5 block text-sm font-medium text-zinc-700 dark:text-zinc-300">{label}</label>
      <div className="relative">
        <input
          id={id}
          ref={ref}
          type={visible ? 'text' : 'password'}
          aria-invalid={!!error}
          aria-describedby={describedBy}
          className={cx(inputClass(!!error), 'pr-11')}
          {...p}
        />
        <button
          type="button"
          onClick={() => setVisible((v) => !v)}
          aria-pressed={visible}
          aria-label={visible ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}
          className="absolute inset-y-0 right-0 grid w-11 place-items-center rounded-r-xl text-zinc-400 hover:text-zinc-700 focus-visible:outline-2 focus-visible:outline-brand-600 dark:hover:text-zinc-200"
        >
          <svg className="size-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
            {visible ? (
              <>
                <path d="M3 3l18 18M10.6 10.6a2 2 0 0 0 2.8 2.8M9.9 5.1A9.8 9.8 0 0 1 12 5c5 0 8.5 4 9.5 7a11 11 0 0 1-2.6 3.9M6.6 6.6A11 11 0 0 0 2.5 12c1 3 4.5 7 9.5 7a9.7 9.7 0 0 0 4.4-1" />
              </>
            ) : (
              <>
                <path d="M2.5 12C3.5 9 7 5 12 5s8.5 4 9.5 7c-1 3-4.5 7-9.5 7s-8.5-4-9.5-7Z" />
                <circle cx="12" cy="12" r="3" />
              </>
            )}
          </svg>
        </button>
      </div>
      {error && <p id={`${id}-err`} className="mt-1.5 text-xs text-red-600 dark:text-red-400">{error}</p>}
      {showRules && (
        <ul id={`${id}-rules`} className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs" aria-label="Yêu cầu mật khẩu">
          {passwordRules.map((r) => {
            const ok = r.test(value)
            return (
              <li key={r.id} className={cx('flex items-center gap-1.5', ok ? 'text-emerald-600 dark:text-emerald-400' : 'text-zinc-500')}>
                <svg className="size-3.5" viewBox="0 0 20 20" fill="currentColor" aria-hidden>
                  {ok ? (
                    <path fillRule="evenodd" d="M16.7 5.3a1 1 0 0 1 0 1.4l-7.5 7.5a1 1 0 0 1-1.4 0L3.3 9.7a1 1 0 1 1 1.4-1.4l3.8 3.8 6.8-6.8a1 1 0 0 1 1.4 0Z" clipRule="evenodd" />
                  ) : (
                    <circle cx="10" cy="10" r="3" />
                  )}
                </svg>
                {r.label}
                <span className="sr-only">{ok ? ' (đã đạt)' : ' (chưa đạt)'}</span>
              </li>
            )
          })}
        </ul>
      )}
      {!error && !showRules && hint && <p id={`${id}-hint`} className="mt-1.5 text-xs text-zinc-500">{hint}</p>}
    </div>
  )
})

export function Divider({ children }: { children: ReactNode }) {
  return (
    <div className="flex items-center gap-3 text-xs uppercase tracking-wide text-zinc-400" role="separator">
      <span className="h-px flex-1 bg-zinc-200 dark:bg-zinc-800" />
      {children}
      <span className="h-px flex-1 bg-zinc-200 dark:bg-zinc-800" />
    </div>
  )
}
