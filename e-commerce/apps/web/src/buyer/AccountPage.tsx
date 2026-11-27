import { Link } from 'react-router-dom'
import { SellerAccountPage } from '../seller/SellerAccountPage'
import { useAuth } from '../shared/auth/AuthContext'
import { AppShell } from '../shared/layout/AppShell'
import { AccountSignInMethods } from '../shared/auth/components/AccountSignInMethods'
import { ChangePasswordForm } from '../shared/auth/components/ChangePasswordForm'
import { roleLabel } from '../shared/auth/roles'
import { PersonalizationSettings } from './PersonalizationSettings'

export default function AccountPage() {
  const { user } = useAuth()
  if (!user) return null
  if (user.role === 'seller') return <SellerAccountPage key={user.id} user={user} />
  const initials = user.full_name.split(/\s+/).slice(-2).map((w) => w[0]).join('').toUpperCase()

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

        {user.role === 'buyer' && (
          <section aria-labelledby="seller-box" className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
            <div>
              <h2 id="seller-box" className="text-lg font-semibold tracking-tight">Bán hàng cùng E-Market</h2>
              <p className="text-sm text-zinc-500">Mở shop miễn phí chỉ với tên shop và nơi bán.</p>
            </div>
            <Link to="/seller/register" className="rounded-xl bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-brand-700">
              Đăng ký bán hàng
            </Link>
          </section>
        )}

        <AccountSignInMethods />
        <ChangePasswordForm />
    </AppShell>
  )
}
