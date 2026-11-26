import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link } from 'react-router-dom'
import { api } from '../../api/client'
import { MarketplaceAuthLayout } from '../components/AuthLayout'
import { Alert, Button, TextField } from '../components/ui'
import { describeError } from '../errors'
import { forgotSchema, type ForgotValues } from '../schemas'

export default function ForgotPasswordPage() {
  const [sentTo, setSentTo] = useState<string>()
  const [formError, setFormError] = useState<string>()
  const { register, handleSubmit, setError, formState: { errors, isSubmitting } } = useForm<ForgotValues>({
    resolver: zodResolver(forgotSchema),
    defaultValues: { email: '' },
  })

  const onSubmit = handleSubmit(async ({ email }) => {
    setFormError(undefined)
    try {
      await api.forgotPassword(email)
      setSentTo(email.trim())
    } catch (e) {
      const d = describeError(e)
      d.fields.forEach((f) => f.field === 'email' && setError('email', { message: f.message }))
      setFormError(d.message)
    }
  })

  return (
    <MarketplaceAuthLayout
      title={sentTo ? 'Kiểm tra hộp thư' : 'Quên mật khẩu'}
      subtitle={sentTo
        ? 'Yêu cầu đặt lại mật khẩu đã được tiếp nhận.'
        : 'Nhập email bạn dùng để đăng ký tài khoản E-Market.'}
      footer={(
        <Link
          to="/login"
          className="inline-flex min-h-11 items-center gap-2 rounded-md font-medium text-[#D93E20] hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#D93E20]"
        >
          <span aria-hidden="true">←</span>
          Quay lại đăng nhập
        </Link>
      )}
    >
      {sentTo ? (
        <div role="status" className="space-y-2 rounded-xl border border-[#CADDD2] bg-[#F4F9F6] p-4 text-[13px] leading-relaxed text-[#285744]">
          <p className="wrap-anywhere">
            Nếu <strong>{sentTo}</strong> đã đăng ký, bạn sẽ nhận được email hướng dẫn đặt lại mật khẩu. Liên kết có hiệu lực trong 60 phút.
          </p>
          <p>Nếu chưa thấy email, hãy kiểm tra thư mục Spam.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {formError && <Alert>{formError}</Alert>}
          <form onSubmit={onSubmit} noValidate className="space-y-5">
            <TextField
              className="login-field"
              label="Email"
              type="email"
              autoComplete="email"
              inputMode="email"
              placeholder="ten@example.com"
              error={errors.email?.message}
              {...register('email')}
            />
            <Button className="login-submit-button" type="submit" loading={isSubmitting}>
              Gửi liên kết đặt lại
            </Button>
          </form>
        </div>
      )}
    </MarketplaceAuthLayout>
  )
}
