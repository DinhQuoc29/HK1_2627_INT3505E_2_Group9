import { useState, type ReactNode } from 'react'
import { SellerIcon, sellerAccountPanel } from '../../../seller/sellerUi'
import type { Provider } from '../../api/client'
import { useAuth } from '../AuthContext'
import { describeError } from '../errors'
import { FacebookMark, FacebookSignIn, facebookAppId } from './FacebookSignIn'
import { GOOGLE_ENABLED, GoogleMark, GoogleSignIn } from './GoogleSignIn'
import { Alert } from './ui'

const providerLabel: Record<Provider, string> = { google: 'Google', facebook: 'Facebook' }
const providers: Provider[] = ['google', 'facebook']
const sellerAction = 'inline-flex min-h-10 items-center justify-center rounded-md border border-slate-200 bg-white px-3 text-[13px] font-medium text-slate-700 transition-colors hover:bg-slate-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-(--seller-accent) disabled:cursor-not-allowed disabled:opacity-60'
const defaultAction = 'rounded-xl border border-zinc-300 px-4 py-2 text-sm font-medium transition hover:bg-zinc-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-zinc-700 dark:hover:bg-zinc-800'

function MethodRow({ title, status, icon, active, seller, children, details }: {
  title: string
  status: string
  icon?: ReactNode
  active?: boolean
  seller: boolean
  children?: ReactNode
  details?: ReactNode
}) {
  return (
    <li>
      <div className="flex flex-wrap items-center justify-between gap-3 py-4">
        <div className="flex min-w-0 items-center gap-3">
          {icon && <span aria-hidden="true" className="grid size-9 shrink-0 place-items-center rounded-md border border-slate-200 bg-slate-50">{icon}</span>}
          <div className="min-w-0">
            <p className={seller ? 'text-[13px] font-semibold text-slate-900' : 'font-medium'}>{title}</p>
            <p className={seller ? `mt-0.5 flex items-center gap-1 text-xs ${active ? 'text-emerald-700' : 'text-slate-500'}` : 'text-sm text-zinc-500'}>
              {seller && active && <SellerIcon name="verified" className="size-3.5" />}
              {status}
            </p>
          </div>
        </div>
        {children}
      </div>
      {details}
    </li>
  )
}

export function AccountSignInMethods({ seller = false, passwordSettings }: {
  seller?: boolean
  passwordSettings?: { action: ReactNode; details: ReactNode }
}) {
  const { user, linkIdentity, unlinkIdentity } = useAuth()
  const [message, setMessage] = useState<{ tone: 'error' | 'success'; text: string }>()
  const [busy, setBusy] = useState(false)
  if (!user) return null

  const onlyMethod = !user.has_password && user.providers.length === 1
  const run = async (action: () => Promise<void>, ok: string) => {
    if (busy) return
    setMessage(undefined)
    setBusy(true)
    try {
      await action()
      setMessage({ tone: 'success', text: ok })
    } catch (error) {
      setMessage({ tone: 'error', text: describeError(error).message ?? 'Không thực hiện được, vui lòng thử lại.' })
    } finally {
      setBusy(false)
    }
  }
  const fail = (text: string) => setMessage({ tone: 'error', text })

  return (
    <section aria-labelledby="login-methods" aria-busy={busy} className={seller
      ? sellerAccountPanel
      : 'rounded-2xl border border-zinc-200 bg-white p-4 shadow-sm sm:p-6 dark:border-zinc-800 dark:bg-zinc-900'}>
      <div className={seller ? 'border-b border-slate-200 pb-3' : undefined}>
        <h2 id="login-methods" className={seller ? 'text-base font-semibold' : 'text-lg font-semibold tracking-tight'}>Phương thức đăng nhập</h2>
        {seller && <p className="mt-0.5 text-[13px] text-slate-500">Quản lý mật khẩu và tài khoản liên kết.</p>}
      </div>
      {message && <div className="mt-4"><Alert tone={message.tone}>{message.text}</Alert></div>}
      <ul className={seller ? 'divide-y divide-slate-200' : 'mt-2 divide-y divide-zinc-200 dark:divide-zinc-800'}>
        <MethodRow
          title="Email và mật khẩu"
          status={user.has_password ? 'Đã thiết lập' : 'Chưa thiết lập'}
          icon={seller && <SellerIcon name="lock" className="size-[18px] text-slate-600" />}
          active={user.has_password}
          seller={seller}
          details={passwordSettings?.details}
        >
          {passwordSettings?.action}
        </MethodRow>
        {providers.map((provider) => {
          const label = providerLabel[provider]
          const linked = user.providers.includes(provider)
          const configured = provider === 'google' ? GOOGLE_ENABLED : Boolean(facebookAppId())
          const connect = (credential: string) => run(() => linkIdentity(provider, credential), `Đã liên kết tài khoản ${label}.`)
          return (
            <MethodRow
              key={provider}
              title={label}
              status={linked ? 'Đã liên kết' : 'Chưa liên kết'}
              icon={seller && (provider === 'google' ? <GoogleMark /> : <span className="text-[#1877F2]"><FacebookMark /></span>)}
              active={linked}
              seller={seller}
            >
              {linked ? (
                <div className="text-right">
                  <button
                    type="button"
                    aria-label={`Hủy liên kết ${label}`}
                    disabled={busy || onlyMethod}
                    onClick={() => run(() => unlinkIdentity(provider), `Đã hủy liên kết ${label}.`)}
                    className={seller ? sellerAction : defaultAction}
                  >
                    Hủy liên kết
                  </button>
                  {onlyMethod && <p className={`mt-1 text-xs ${seller ? 'text-slate-500' : 'text-zinc-500'}`}>Đây là cách đăng nhập duy nhất của bạn.</p>}
                </div>
              ) : seller && !configured ? (
                <button type="button" className={sellerAction} disabled>Tiếp tục với {label}</button>
              ) : (
                <div className={seller ? 'w-full min-w-0 sm:w-[220px]' : 'w-full min-w-0 sm:w-[260px]'}>
                  {provider === 'google' ? (
                    <GoogleSignIn width={seller ? 220 : 260} appearance={seller ? 'reference' : 'default'} onCredential={connect} onError={() => fail('Không thể liên kết Google. Vui lòng thử lại.')} />
                  ) : (
                    <FacebookSignIn appearance={seller ? 'reference' : 'default'} onToken={connect} onError={fail} />
                  )}
                </div>
              )}
            </MethodRow>
          )
        })}
      </ul>
    </section>
  )
}
