import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../shared/auth/AuthContext'
import { Logo } from '../shared/auth/components/AuthLayout'
import type { Provider } from '../shared/api/client'
import { FacebookSignIn } from '../shared/auth/components/FacebookSignIn'
import { GoogleSignIn } from '../shared/auth/components/GoogleSignIn'
import { Alert, Button } from '../shared/auth/components/ui'
import { describeError } from '../shared/auth/errors'

const providerLabel: Record<Provider, string> = { google: 'Google', facebook: 'Facebook' }
const roleLabel = { buyer: 'Người mua', seller: 'Người bán', admin: 'Quản trị viên' } as const

function Row({ title, status, children }: { title: string; status: string; children?: React.ReactNode }) {
  return (
    <li className="flex flex-wrap items-center justify-between gap-3 py-4">
      <div>
        <p className="font-medium">{title}</p>
        <p className="text-sm text-zinc-500">{status}</p>
      </div>
      {children}
    </li>
  )
}

export default function AccountPage() {
  const { user, logout, linkIdentity, unlinkIdentity } = useAuth()
  const navigate = useNavigate()
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
    <div className="min-h-full bg-zinc-50 dark:bg-zinc-950">
      <header className="border-b border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900">
        <div className="mx-auto flex h-16 max-w-3xl items-center justify-between px-5"><Logo /></div>
      </header>
      <main className="mx-auto max-w-3xl space-y-6 px-5 py-10">
        <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
          <div className="flex items-center gap-4">
            <span className="grid size-14 place-items-center rounded-full bg-brand-100 text-lg font-bold text-brand-700" aria-hidden>{initials}</span>
            <div>
              <h1 className="text-xl font-bold tracking-tight">Xin chào, {user.full_name}</h1>
              <p className="text-sm text-zinc-500">{user.email}</p>
            </div>
          </div>
          <dl className="mt-6 grid gap-4 text-sm sm:grid-cols-2">
            <div><dt className="text-zinc-500">Vai trò</dt><dd className="mt-0.5 font-medium">{roleLabel[user.role]}</dd></div>
            <div><dt className="text-zinc-500">Tham gia từ</dt><dd className="mt-0.5 font-medium">{new Date(user.created_at).toLocaleDateString('vi-VN')}</dd></div>
          </dl>
        </section>

        <section aria-labelledby="login-methods" className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
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
                    <div className="w-full sm:w-[260px]">
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

        <div className="max-w-[200px]">
          <Button type="button" onClick={async () => { await logout(); navigate('/login', { replace: true }) }}>Đăng xuất</Button>
        </div>
      </main>
    </div>
  )
}
