import { zodResolver } from '@hookform/resolvers/zod'
import { useId, useState } from 'react'
import { useForm, useWatch } from 'react-hook-form'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../AuthContext'
import { MarketplaceAuthLayout } from '../components/AuthLayout'
import { SocialSignIn } from '../components/SocialSignIn'
import { Alert, Button, Divider, PasswordField, TextField } from '../components/ui'
import { describeError, safeRedirect } from '../errors'
import { homeFor } from '../roles'
import { registerSchema, type RegisterValues } from '../schemas'

export default function RegisterPage() {
  const { register: signUp, loginWithGoogle, loginWithFacebook } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [formError, setFormError] = useState<string>()
  const [socialBusy, setSocialBusy] = useState(false)
  const [acceptedTerms, setAcceptedTerms] = useState(false)
  const [termsError, setTermsError] = useState(false)
  const termsErrorId = useId()
  const from = (location.state as { from?: string } | null)?.from
  const dest = (u: { role: Parameters<typeof homeFor>[0] }) => safeRedirect(from, homeFor(u.role))

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
    if (!acceptedTerms) {
      setTermsError(true)
      return
    }
    setFormError(undefined)
    try {
      navigate(dest(await signUp(v)), { replace: true })
    } catch (e) { fail(e) }
  })

  const social = (fn: (token: string) => Promise<{ role: Parameters<typeof homeFor>[0] }>) => async (token: string) => {
    setFormError(undefined)
    setSocialBusy(true)
    try {
      navigate(dest(await fn(token)), { replace: true })
    } catch (e) { fail(e) } finally { setSocialBusy(false) }
  }

  return (
    <MarketplaceAuthLayout
      title="Tạo tài khoản"
      subtitle="Chỉ mất một phút để bắt đầu mua sắm."
      footer={<>Đã có tài khoản? <Link to="/login" state={location.state} className="ml-1 font-medium text-[#D93E20] hover:underline">Đăng nhập</Link></>}
    >
      <div className="space-y-4">
        {formError && <Alert>{formError}</Alert>}
        <form onSubmit={onSubmit} noValidate className="space-y-4">
          <TextField className="login-field" label="Họ và tên" autoComplete="name" placeholder="Nguyễn Văn An" error={errors.full_name?.message} {...register('full_name')} />
          <TextField className="login-field" label="Email" type="email" autoComplete="email" inputMode="email" placeholder="ban@example.com" error={errors.email?.message} {...register('email')} />
          <PasswordField className="login-field" label="Mật khẩu" autoComplete="new-password" placeholder="Tạo mật khẩu" showRules value={password} error={errors.password?.message} {...register('password')} />
          <PasswordField className="login-field" label="Nhập lại mật khẩu" autoComplete="new-password" placeholder="Nhập lại mật khẩu" error={errors.confirm?.message} {...register('confirm')} />
          <div>
            <label className="flex cursor-pointer items-start gap-3 text-xs leading-relaxed text-[#71717A]">
              <input
                type="checkbox"
                checked={acceptedTerms}
                aria-invalid={termsError}
                aria-describedby={termsError ? termsErrorId : undefined}
                onChange={(event) => {
                  setAcceptedTerms(event.target.checked)
                  setTermsError(false)
                }}
                className="mt-0.5 size-4 shrink-0 accent-[#D93E20]"
              />
              <span>Tôi đồng ý với điều khoản sử dụng của E-Market.</span>
            </label>
            {termsError && (
              <p id={termsErrorId} role="alert" className="auth-field-error mt-1.5 pl-7 text-xs">
                Vui lòng xác nhận điều khoản trước khi tạo tài khoản.
              </p>
            )}
          </div>
          <Button className="login-submit-button" type="submit" loading={isSubmitting}>Tạo tài khoản</Button>
        </form>
        <div aria-busy={socialBusy} className={`space-y-5 pt-2 ${socialBusy ? 'pointer-events-none opacity-60' : ''}`}>
          <Divider className="login-divider">hoặc</Divider>
          <SocialSignIn mode="signup" layout="inline" onGoogle={social(loginWithGoogle)} onFacebook={social(loginWithFacebook)} onError={setFormError} />
        </div>
      </div>
    </MarketplaceAuthLayout>
  )
}
