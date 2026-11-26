import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../shared/auth/AuthContext'
import { AppShell } from '../shared/layout/AppShell'
import { ChangePasswordForm } from '../shared/auth/components/ChangePasswordForm'
import { roleLabel } from '../shared/auth/roles'
import type { Provider } from '../shared/api/client'
import { FacebookSignIn } from '../shared/auth/components/FacebookSignIn'
import { GoogleSignIn } from '../shared/auth/components/GoogleSignIn'
import { Alert } from '../shared/auth/components/ui'
import { describeError } from '../shared/auth/errors'
import { PersonalizationSettings } from './PersonalizationSettings'

const providerLabel: Record<Provider, string> = { google: 'Google', facebook: 'Facebook' }

function Row({ title, status, children }: { title: string; status: string; children?: React.ReactNode }) {
  return (
    <li className="flex flex-wrap items-center justify-between gap-3 py-4">
      <div className="min-w-0">
        <p className="font-medium">{title}</p>
        <p className="text-sm text-zinc-500">{status}</p>
      </div>
      {children}
    </li>
  )
}

export default function AccountPage() {
  const { user, linkIdentity, unlinkIdentity } = useAuth()
  const [message, setMessage] = useState<{ tone: 'error' | 'success'; text: string }>()
  const [busy, setBusy] = useState(false)
  if (!user) return null
  const initials = user.full_name.split(/\s+/).slice(-2).map((w) => w[0]).join('').toUpperCase()

  const run = async (action: () => Promise<void>, ok: string) => {
    setMessage(undefined)
    setBusy(true)
    try {
      await action()
      setMessage({ tone: 'success', text: ok })
    } catch (e) {
      setMessage({ tone: 'error', text: describeError(e).message ?? 'Không thực hiện được, vui lòng thử lại.' })
    } finally { setBusy(false) }
  }

  return (
    <AppShell>
        <section className="rounded-2xl border border-zinc-200 bg-white p-4 shadow-sm sm:p-6 dark:border-zinc-800 dark:bg-zinc-900">
          <div className="flex items-center gap-4">
            <span className="grid size-12 shrink-0 place-items-center rounded-full bg-brand-100 text-lg font-bold text-brand-700 sm:size-14" aria-hidden>{initials}</span>
            <div className="min-w-0 wrap-anywhere">
              <h1 className="text-xl font-bold tracking-tight">Xin chào, {user.full_name}</h1>
              <p className="text-sm text-zinc-500">{user.email}</p>
            </div>
          </div>
          <dl className="mt-6 grid gap-4 text-sm sm:grid-cols-2">
            <div><dt className="text-zinc-500">Vai trò</dt><dd className="mt-0.5 font-medium">{roleLabel[user.role]}</dd></div>
            <div><dt className="text-zinc-500">Email</dt><dd className="mt-0.5 font-medium">{user.email_verified ? 'Đã xác minh' : 'Chưa xác minh'}</dd></div>
            <div><dt className="text-zinc-500">Tham gia từ</dt><dd className="mt-0.5 font-medium">{new Date(user.created_at).toLocaleDateString('vi-VN')}</dd></div>
          </dl>
        </section>

        {user.role === 'buyer' && <PersonalizationSettings key={user.id} />}

        {user.role !== 'admin' && (
          <section aria-labelledby="seller-box" className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
            <div>
              <h2 id="seller-box" className="text-lg font-semibold tracking-tight">{user.role === 'seller' ? 'Shop của bạn' : 'Bán hàng cùng E-Market'}</h2>
              <p className="text-sm text-zinc-500">{user.role === 'seller' ? 'Xem và quản lý gian hàng của bạn.' : 'Mở shop miễn phí chỉ với tên shop và nơi bán.'}</p>
            </div>
            <Link to={user.role === 'seller' ? '/seller' : '/seller/register'} className="rounded-xl bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-brand-700">
              {user.role === 'seller' ? 'Vào shop' : 'Đăng ký bán hàng'}
            </Link>
          </section>
        )}

        <section aria-labelledby="login-methods" className="rounded-2xl border border-zinc-200 bg-white p-4 shadow-sm sm:p-6 dark:border-zinc-800 dark:bg-zinc-900">
          <h2 id="login-methods" className="text-lg font-semibold tracking-tight">Phương thức đăng nhập</h2>
          {message && <div className="mt-4"><Alert tone={message.tone}>{message.text}</Alert></div>}
          <ul className="mt-2 divide-y divide-zinc-200 dark:divide-zinc-800">
            <Row title="Email và mật khẩu" status={user.has_password ? 'Đã thiết lập' : 'Chưa thiết lập – bạn đang đăng nhập bằng Google'} />
            {(['google', 'facebook'] as Provider[]).map((p) => {
              const linked = user.providers.includes(p)
              const onlyMethod = !user.has_password && user.providers.length === 1
              const fail = (text: string) => setMessage({ tone: 'error', text })
              return (
                <Row key={p} title={providerLabel[p]} status={linked ? 'Đã liên kết' : 'Chưa liên kết'}>
                  {linked ? (
                    <div className="text-right">
                      <button
                        type="button"
                        aria-label={`Hủy liên kết ${providerLabel[p]}`}
                        disabled={busy || onlyMethod}
                        onClick={() => run(() => unlinkIdentity(p), `Đã hủy liên kết ${providerLabel[p]}.`)}
                        className="rounded-xl border border-zinc-300 px-4 py-2 text-sm font-medium transition hover:bg-zinc-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-zinc-700 dark:hover:bg-zinc-800"
                      >
                        Hủy liên kết
                      </button>
                      {onlyMethod && <p className="mt-1 text-xs text-zinc-500">Đây là cách đăng nhập duy nhất của bạn.</p>}
                    </div>
                  ) : (
                    <div className="w-full min-w-0 sm:w-[260px]">
                      {p === 'google' ? (
                        <GoogleSignIn width={260} onCredential={(c) => run(() => linkIdentity(p, c), 'Đã liên kết tài khoản Google.')} onError={() => fail('Không thể liên kết Google. Vui lòng thử lại.')} />
                      ) : (
                        <FacebookSignIn onToken={(c) => run(() => linkIdentity(p, c), 'Đã liên kết tài khoản Facebook.')} onError={fail} />
                      )}
                    </div>
                  )}
                </Row>
              )
            })}
          </ul>
        </section>

        <ChangePasswordForm />
    </AppShell>
  )
}
