import { useEffect, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api } from '../../api/client'
import { useAuth } from '../AuthContext'
import { AuthLayout } from '../components/AuthLayout'
import { Alert, Spinner } from '../components/ui'
import { describeError } from '../errors'
import { homeFor } from '../roles'

/** Trang đích của liên kết trong email xác minh. Token dùng một lần nên chỉ gọi API đúng một lần. */
export default function VerifyEmailPage() {
  const token = useSearchParams()[0].get('token') ?? ''
  const { status, user, refreshUser } = useAuth()
  const [result, setResult] = useState<{ ok: boolean; message?: string } | null>(token ? null : { ok: false, message: 'Liên kết không hợp lệ.' })
  const started = useRef(false)
  const refreshed = useRef(false)

  useEffect(() => {
    if (!token || started.current) return
    started.current = true
    api.confirmEmail(token).then(
      () => setResult({ ok: true }),
      (e) => setResult({ ok: false, message: describeError(e).message }),
    )
  }, [token])

  // Đã đăng nhập thì tải lại hồ sơ để biểu ngữ "chưa xác minh" biến mất.
  useEffect(() => {
    if (result?.ok && status === 'authenticated' && !refreshed.current) {
      refreshed.current = true
      void refreshUser()
    }
  }, [result, status, refreshUser])

  return (
    <AuthLayout
      title="Xác minh email"
      subtitle="Hoàn tất việc xác nhận địa chỉ email của bạn."
      footer={<Link to={user ? homeFor(user.role) : '/login'} className="font-semibold text-brand-600 hover:underline">{user ? 'Về trang của tôi' : 'Đến trang đăng nhập'}</Link>}
    >
      {result === null ? <Spinner label="Đang xác minh…" /> : result.ok ? (
        <Alert tone="success">Email của bạn đã được xác minh. Cảm ơn bạn!</Alert>
      ) : (
        <Alert>{result.message} {user && 'Bạn có thể gửi lại email xác minh từ biểu ngữ ở đầu trang tài khoản.'}</Alert>
      )}
    </AuthLayout>
  )
}
