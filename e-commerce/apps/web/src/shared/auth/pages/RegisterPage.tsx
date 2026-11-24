import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm, useWatch } from 'react-hook-form'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../AuthContext'
import { AuthLayout } from '../components/AuthLayout'
import { GoogleSignIn } from '../components/GoogleSignIn'
import { Alert, Button, Divider, PasswordField, TextField } from '../components/ui'
import { describeError, safeRedirect } from '../errors'
import { registerSchema, type RegisterValues } from '../schemas'

export default function RegisterPage() {
  const { register: signUp, loginWithGoogle } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [formError, setFormError] = useState<string>()
  const to = safeRedirect((location.state as { from?: string } | null)?.from)

  const { register, handleSubmit, setError, control, formState: { errors, isSubmitting } } = useForm<RegisterValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: { full_name: '', email: '', password: '', confirm: '' },
  })
  const password = useWatch({ control, name: 'password' })

  const fail = (e: unknown) => {
    const d = describeError(e)
    d.fields.forEach((f) => ['full_name', 'email', 'password'].includes(f.field) && setError(f.field as keyof RegisterValues, { message: f.message }))
    setFormError(d.message)
  }

  const onSubmit = handleSubmit(async ({ confirm: _confirm, ...v }) => {
    setFormError(undefined)
    try {
      await signUp(v)
      navigate(to, { replace: true })
    } catch (e) { fail(e) }
  })

  const onGoogle = async (credential: string) => {
    setFormError(undefined)
    try {
      await loginWithGoogle(credential)
      navigate(to, { replace: true })
    } catch (e) { fail(e) }
  }

  return (
    <AuthLayout
      title="Tạo tài khoản"
      subtitle="Chỉ mất một phút để bắt đầu mua sắm."
      footer={<>Đã có tài khoản? <Link to="/login" state={location.state} className="font-semibold text-brand-600 hover:underline">Đăng nhập</Link></>}
    >
      {formError && <Alert>{formError}</Alert>}
      <GoogleSignIn onCredential={onGoogle} onError={() => setFormError('Không thể đăng ký bằng Google. Vui lòng thử lại.')} />
      <Divider>hoặc dùng email</Divider>
      <form onSubmit={onSubmit} noValidate className="space-y-4">
        <TextField label="Họ và tên" autoComplete="name" placeholder="Nguyễn Văn An" autoFocus error={errors.full_name?.message} {...register('full_name')} />
        <TextField label="Email" type="email" autoComplete="email" inputMode="email" placeholder="ban@example.com" error={errors.email?.message} {...register('email')} />
        <PasswordField label="Mật khẩu" autoComplete="new-password" placeholder="Tạo mật khẩu" showRules value={password} error={errors.password?.message} {...register('password')} />
        <PasswordField label="Nhập lại mật khẩu" autoComplete="new-password" placeholder="Nhập lại mật khẩu" error={errors.confirm?.message} {...register('confirm')} />
        <Button type="submit" loading={isSubmitting}>Tạo tài khoản</Button>
      </form>
      <p className="text-center text-xs text-zinc-500">Bằng việc đăng ký, bạn đồng ý với điều khoản sử dụng của {`E-Market`}.</p>
    </AuthLayout>
  )
}
