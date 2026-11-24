import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../AuthContext'
import { AuthLayout } from '../components/AuthLayout'
import { GoogleSignIn } from '../components/GoogleSignIn'
import { Alert, Button, Divider, PasswordField, TextField } from '../components/ui'
import { describeError, safeRedirect } from '../errors'
import { loginSchema, type LoginValues } from '../schemas'

export default function LoginPage() {
  const { login, loginWithGoogle } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [formError, setFormError] = useState<string>()
  const [googleBusy, setGoogleBusy] = useState(false)
  const to = safeRedirect((location.state as { from?: string } | null)?.from)

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
      await login(v)
      navigate(to, { replace: true })
    } catch (e) { fail(e) }
  })

  const onGoogle = async (credential: string) => {
    setFormError(undefined)
    setGoogleBusy(true)
    try {
      await loginWithGoogle(credential)
      navigate(to, { replace: true })
    } catch (e) { fail(e) } finally { setGoogleBusy(false) }
  }

  return (
    <AuthLayout
      title="Chào mừng trở lại"
      subtitle="Đăng nhập để tiếp tục mua sắm và theo dõi đơn hàng."
      footer={<>Chưa có tài khoản? <Link to="/register" state={location.state} className="font-semibold text-brand-600 hover:underline">Đăng ký</Link></>}
    >
      {formError && <Alert>{formError}</Alert>}
      <form onSubmit={onSubmit} noValidate className="space-y-4">
        <TextField label="Email" type="email" autoComplete="email" inputMode="email" placeholder="ban@example.com" autoFocus error={errors.email?.message} {...register('email')} />
        <PasswordField label="Mật khẩu" autoComplete="current-password" placeholder="Nhập mật khẩu" error={errors.password?.message} {...register('password')} />
        <Button type="submit" loading={isSubmitting}>Đăng nhập</Button>
      </form>
      <Divider>hoặc</Divider>
      <div aria-busy={googleBusy} className={googleBusy ? 'pointer-events-none opacity-60' : undefined}>
        <GoogleSignIn onCredential={onGoogle} onError={() => setFormError('Không thể đăng nhập bằng Google. Vui lòng thử lại.')} />
      </div>
    </AuthLayout>
  )
}
