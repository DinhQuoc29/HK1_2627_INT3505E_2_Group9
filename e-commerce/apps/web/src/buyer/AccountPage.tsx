import { useNavigate } from 'react-router-dom'
import { useAuth } from '../shared/auth/AuthContext'
import { Logo } from '../shared/auth/components/AuthLayout'
import { Button } from '../shared/auth/components/ui'

const roleLabel = { buyer: 'Người mua', seller: 'Người bán', admin: 'Quản trị viên' } as const

export default function AccountPage() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  if (!user) return null
  const initials = user.full_name.split(/\s+/).slice(-2).map((w) => w[0]).join('').toUpperCase()

  return (
    <div className="min-h-full bg-zinc-50 dark:bg-zinc-950">
      <header className="border-b border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900">
        <div className="mx-auto flex h-16 max-w-3xl items-center justify-between px-5"><Logo /></div>
      </header>
      <main className="mx-auto max-w-3xl px-5 py-10">
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
          <div className="mt-8 max-w-[200px]">
            <Button type="button" onClick={async () => { await logout(); navigate('/login', { replace: true }) }}>Đăng xuất</Button>
          </div>
        </section>
      </main>
    </div>
  )
}
