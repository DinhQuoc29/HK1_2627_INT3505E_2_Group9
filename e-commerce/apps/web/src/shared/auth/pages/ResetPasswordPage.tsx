import { zodResolver } from '@hookform/resolvers/zod'
import { useEffect, useState } from 'react'
import { useForm, useWatch } from 'react-hook-form'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { ApiError, api } from '../../api/client'
import { MarketplaceAuthLayout } from '../components/AuthLayout'
import { Alert, Button, PasswordField } from '../components/ui'
import { describeError } from '../errors'
import { resetSchema, type ResetValues } from '../schemas'

export default function ResetPasswordPage() {
  const token = useSearchParams()[0].get('token') ?? ''
  const navigate = useNavigate()
  const [formError, setFormError] = useState<string>()
  const [rejectedToken, setRejectedToken] = useState<string>()
  const [completedToken, setCompletedToken] = useState<string>()
  const { register, handleSubmit, reset, setError, control, formState: { errors, isSubmitting } } = useForm<ResetValues>({
    resolver: zodResolver(resetSchema),
    defaultValues: { new_password: '', confirm: '' },
  })
  const password = useWatch({ control, name: 'new_password' })
  const invalidLink = !token || token === rejectedToken
  const done = token === completedToken

  useEffect(() => {
    if (!done) return
    const timer = window.setTimeout(() => navigate('/login', { replace: true }), 2500)
    return () => window.clearTimeout(timer)
  }, [done, navigate])

  const onSubmit = handleSubmit(async ({ new_password }) => {
    setFormError(undefined)
    try {
      await api.resetPassword(token, new_password)
      setCompletedToken(token)
      reset()
    } catch (e) {
      if (e instanceof ApiError && e.slug === 'invalid-reset-token') {
        setRejectedToken(token)
        reset()
        return
      }
      const d = describeError(e)
      d.fields.forEach((f) => f.field === 'new_password' && setError('new_password', { message: f.message }))
      setFormError(d.message)
    }
  })

  return (
    <MarketplaceAuthLayout
      title="Đặt lại mật khẩu"
      subtitle={invalidLink
        ? 'Yêu cầu liên kết mới qua email để tiếp tục.'
        : done ? 'Bạn có thể đăng nhập bằng mật khẩu mới.' : 'Chọn mật khẩu mới cho tài khoản của bạn.'}
      footer={
        <Link
          to="/login"
          className="inline-flex min-h-11 items-center gap-2 rounded-md font-medium text-[#D93E20] hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#D93E20]"
        >
          <span aria-hidden="true">←</span>
          Về trang đăng nhập
        </Link>
      }
    >
      {invalidLink ? (
        <Alert>
          <p>{token ? 'Liên kết đặt lại mật khẩu không hợp lệ hoặc đã hết hạn.' : 'Liên kết không hợp lệ.'}</p>
          <Link to="/forgot-password" className="mt-1 inline-block font-semibold underline underline-offset-2">
            Yêu cầu liên kết mới
          </Link>
        </Alert>
      ) : done ? (
        <Alert tone="success">Đã đổi mật khẩu. Đang chuyển tới trang đăng nhập…</Alert>
      ) : (
        <div className="space-y-4">
          {formError && <Alert>{formError}</Alert>}
          <form onSubmit={onSubmit} noValidate className="space-y-5">
            <PasswordField
              className="login-field"
              label="Mật khẩu mới"
              autoComplete="new-password"
              placeholder="Nhập mật khẩu mới"
              showRules
              value={password}
              error={errors.new_password?.message}
              {...register('new_password')}
            />
            <PasswordField
              className="login-field"
              label="Nhập lại mật khẩu mới"
              autoComplete="new-password"
              placeholder="Xác nhận mật khẩu mới"
              error={errors.confirm?.message}
              {...register('confirm')}
            />
            <Button className="login-submit-button" type="submit" loading={isSubmitting}>Đổi mật khẩu</Button>
          </form>
        </div>
      )}
    </MarketplaceAuthLayout>
  )
}
