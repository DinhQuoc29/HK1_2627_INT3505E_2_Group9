import { useId, useState } from 'react'
import { Link } from 'react-router-dom'
import type { User } from '../shared/api/client'
import { AccountSignInMethods } from '../shared/auth/components/AccountSignInMethods'
import { ChangePasswordForm } from '../shared/auth/components/ChangePasswordForm'
import { AppShell } from '../shared/layout/AppShell'
import { SellerIcon, SellerInitials, sellerAccountPanel } from './sellerUi'

const joinedDate = new Intl.DateTimeFormat('vi-VN', {
  day: '2-digit',
  month: '2-digit',
  year: 'numeric',
  timeZone: 'Asia/Ho_Chi_Minh',
})
const focus = 'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-(--seller-accent)'
const label = 'text-xs font-medium tracking-wide text-slate-500 uppercase'

export function SellerAccountPage({ user }: { user: User }) {
  const [passwordOpen, setPasswordOpen] = useState(false)
  const passwordPanelId = useId()

  return (
    <AppShell>
      <div>
        <h1 className="text-[22px] leading-7 font-semibold tracking-tight">Tài khoản</h1>
        <p className="mt-0.5 text-[13px] leading-5 text-slate-500">Quản lý thông tin cá nhân và phương thức đăng nhập.</p>
      </div>

      <section aria-labelledby="seller-profile" className={sellerAccountPanel}>
        <div className="flex items-center gap-3.5 border-b border-slate-200 pb-4">
          <span aria-hidden="true" className="grid size-13 shrink-0 place-items-center rounded-full bg-slate-900 text-base font-bold tracking-tight text-white">
            <SellerInitials name={user.full_name} />
          </span>
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <h2 id="seller-profile" className="text-base font-semibold tracking-tight wrap-anywhere">{user.full_name}</h2>
              <span className="rounded-full border border-slate-200 bg-slate-50 px-2 py-0.5 text-[11px] font-medium text-slate-600">Người bán</span>
            </div>
            <p className="mt-0.5 text-[13px] text-slate-500 wrap-anywhere">{user.email}</p>
          </div>
        </div>
        <dl className="grid grid-cols-2 gap-x-4 gap-y-3 pt-4 sm:grid-cols-3">
          <div>
            <dt className={label}>Vai trò</dt>
            <dd className="mt-1 text-[13px] font-medium">Người bán</dd>
          </div>
          <div>
            <dt className={label}>Email liên hệ</dt>
            <dd className={`mt-1 flex items-center gap-1.5 text-[13px] font-medium ${user.email_verified ? 'text-emerald-700' : 'text-amber-800'}`}>
              {user.email_verified && <SellerIcon name="verified" className="size-4" />}
              {user.email_verified ? 'Đã xác minh' : 'Chưa xác minh'}
            </dd>
          </div>
          <div>
            <dt className={label}>Tham gia từ</dt>
            <dd className="mt-1 text-[13px] font-medium tabular-nums">
              <time dateTime={user.created_at}>{joinedDate.format(new Date(user.created_at))}</time>
            </dd>
          </div>
        </dl>
      </section>

      <section aria-labelledby="seller-shop-link" className={`${sellerAccountPanel} flex flex-wrap items-center justify-between gap-3`}>
        <div className="flex min-w-0 items-center gap-3.5">
          <span className="grid size-10 shrink-0 place-items-center rounded-lg bg-(--seller-nav-active) text-brand-700">
            <SellerIcon name="storefront" className="size-5" />
          </span>
          <div>
            <h2 id="seller-shop-link" className="text-base font-semibold">Shop của bạn</h2>
            <p className="mt-0.5 text-[13px] text-slate-500">Xem và quản lý gian hàng của bạn.</p>
          </div>
        </div>
        <Link to="/seller" className={`inline-flex min-h-11 shrink-0 items-center gap-1.5 rounded-md bg-(--seller-accent) px-3.5 text-[13px] font-semibold text-white shadow-xs transition-colors hover:bg-[#D94325] sm:min-h-9 ${focus}`}>
          Vào shop <SellerIcon name="arrow" className="size-4" />
        </Link>
      </section>

      <AccountSignInMethods
        seller
        passwordSettings={{
          action: (
            <button
              type="button"
              aria-expanded={passwordOpen}
              aria-controls={passwordPanelId}
              className={`inline-flex min-h-10 items-center rounded-md border border-slate-200 bg-white px-3 text-[13px] font-medium text-slate-700 transition-colors hover:bg-slate-50 ${focus}`}
              onClick={() => setPasswordOpen((open) => !open)}
            >
              {passwordOpen ? 'Đóng biểu mẫu' : user.has_password ? 'Đổi mật khẩu' : 'Đặt mật khẩu'}
            </button>
          ),
          details: (
            <div id={passwordPanelId} hidden={!passwordOpen} className="pb-4">
              {passwordOpen && <ChangePasswordForm embedded />}
            </div>
          ),
        }}
      />
    </AppShell>
  )
}
