import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../AuthContext'
import { MarketplaceAuthLayout } from '../components/AuthLayout'
import { SocialSignIn } from '../components/SocialSignIn'
import { Alert, Button, Divider, PasswordField, TextField } from '../components/ui'
import { describeError, safeRedirect } from '../errors'
import { homeFor } from '../roles'
import { loginSchema, type LoginValues } from '../schemas'

export default function LoginPage() {
  const { login, loginWithGoogle, loginWithFacebook, notice } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [formError, setFormError] = useState<string>()
  const [googleBusy, setGoogleBusy] = useState(false)
  const from = (location.state as { from?: string } | null)?.from
  const dest = (u: { role: Parameters<typeof homeFor>[0] }) => safeRedirect(from, homeFor(u.role))

  const { register, handleSubmit, setError, formState: { errors, isSubmitting } } = useForm<LoginValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: '', password: '' },
  })

  const fail = (e: unknown) => {
    const d = describeError(e)
    d.fields.forEach((f) => (f.field === 'email' || f.field === 'password') && setError(f.field, { message: f.message }))
    setFormError(d.message)
  }

  const onSubmit = handleSubmit(async (v) => {
    setFormError(undefined)
    try {
      navigate(dest(await login(v)), { replace: true })
    } catch (e) { fail(e) }
  })

  const social = (fn: (token: string) => Promise<{ role: Parameters<typeof homeFor>[0] }>) => async (token: string) => {
    setFormError(undefined)
    setGoogleBusy(true)
    try {
      navigate(dest(await fn(token)), { replace: true })
    } catch (e) { fail(e) } finally { setGoogleBusy(false) }
  }

  return (
    <MarketplaceAuthLayout
      title="Chào mừng trở lại"
      subtitle="Đăng nhập để tiếp tục mua sắm cùng E-Market."
      footer={<>Chưa có tài khoản? <Link to="/register" state={location.state} className="ml-1 font-medium text-[#D93E20] hover:underline">Đăng ký ngay</Link></>}
    >
      <div className="space-y-4">
        {notice && !formError && <Alert tone="info">{notice}</Alert>}
        {formError && <Alert className="login-error-alert">{formError}</Alert>}
        <form onSubmit={onSubmit} noValidate className="login-form space-y-5">
          <TextField className="login-field" label="Email" type="email" autoComplete="email" inputMode="email" placeholder="ten@example.com" error={errors.email?.message} {...register('email')} />
          <PasswordField
            className="login-field"
            label="Mật khẩu"
            labelAction={<Link to="/forgot-password" className="text-xs font-medium text-[#71717A] transition-colors hover:text-[#18181B]">Quên mật khẩu?</Link>}
            autoComplete="current-password"
            placeholder="Nhập mật khẩu của bạn"
            error={errors.password?.message}
            {...register('password')}
          />
          <Button className="login-submit-button" type="submit" loading={isSubmitting}>Đăng nhập</Button>
        </form>
        <div aria-busy={googleBusy} className={`space-y-5 pt-2 ${googleBusy ? 'pointer-events-none opacity-60' : ''}`}>
          <Divider className="login-divider">hoặc</Divider>
          <SocialSignIn mode="signin" layout="inline" onGoogle={social(loginWithGoogle)} onFacebook={social(loginWithFacebook)} onError={setFormError} />
        </div>
      </div>
    </MarketplaceAuthLayout>
  )
}
