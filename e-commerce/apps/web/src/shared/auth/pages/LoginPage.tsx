import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../AuthContext'
import { AuthLayout } from '../components/AuthLayout'
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
    <AuthLayout
      title="Chào mừng trở lại"
      subtitle="Đăng nhập để tiếp tục mua sắm và theo dõi đơn hàng."
      footer={<>Chưa có tài khoản? <Link to="/register" state={location.state} className="font-semibold text-brand-600 hover:underline">Đăng ký</Link></>}
    >
      {notice && !formError && <Alert tone="info">{notice}</Alert>}
      {formError && <Alert>{formError}</Alert>}
      <form onSubmit={onSubmit} noValidate className="space-y-4">
        <TextField label="Email" type="email" autoComplete="email" inputMode="email" placeholder="ban@example.com" autoFocus error={errors.email?.message} {...register('email')} />
        <PasswordField label="Mật khẩu" autoComplete="current-password" placeholder="Nhập mật khẩu" error={errors.password?.message} {...register('password')} />
        <div className="-mt-2 text-right"><Link to="/forgot-password" className="text-sm font-medium text-brand-600 hover:underline">Quên mật khẩu?</Link></div>
        <Button type="submit" loading={isSubmitting}>Đăng nhập</Button>
      </form>
      <Divider>hoặc</Divider>
      <div aria-busy={googleBusy} className={googleBusy ? 'pointer-events-none opacity-60' : undefined}>
        <SocialSignIn mode="signin" onGoogle={social(loginWithGoogle)} onFacebook={social(loginWithFacebook)} onError={setFormError} />
      </div>
    </AuthLayout>
  )
}
