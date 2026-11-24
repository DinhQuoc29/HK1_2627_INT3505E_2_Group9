import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm, useWatch } from 'react-hook-form'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { api } from '../../api/client'
import { AuthLayout } from '../components/AuthLayout'
import { Alert, Button, PasswordField } from '../components/ui'
import { describeError } from '../errors'
import { resetSchema, type ResetValues } from '../schemas'

export default function ResetPasswordPage() {
  const token = useSearchParams()[0].get('token') ?? ''
  const navigate = useNavigate()
  const [formError, setFormError] = useState<string>()
  const [done, setDone] = useState(false)
  const { register, handleSubmit, setError, control, formState: { errors, isSubmitting } } = useForm<ResetValues>({
    resolver: zodResolver(resetSchema),
    defaultValues: { new_password: '', confirm: '' },
  })
  const password = useWatch({ control, name: 'new_password' })

  const onSubmit = handleSubmit(async ({ new_password }) => {
    setFormError(undefined)
    try {
      await api.resetPassword(token, new_password)
      setDone(true)
      setTimeout(() => navigate('/login', { replace: true }), 2500)
    } catch (e) {
      const d = describeError(e)
      d.fields.forEach((f) => f.field === 'new_password' && setError('new_password', { message: f.message }))
      setFormError(d.message)
    }
  })

  return (
    <AuthLayout
      title="Đặt lại mật khẩu"
      subtitle="Chọn mật khẩu mới cho tài khoản của bạn."
      footer={<Link to="/login" className="font-semibold text-brand-600 hover:underline">Về trang đăng nhập</Link>}
    >
      {!token ? (
        <Alert>Liên kết không hợp lệ. Hãy <Link to="/forgot-password" className="font-semibold underline">yêu cầu liên kết mới</Link>.</Alert>
      ) : done ? (
        <Alert tone="success">Đã đổi mật khẩu. Đang chuyển tới trang đăng nhập…</Alert>
      ) : (
        <>
          {formError && <Alert>{formError} <Link to="/forgot-password" className="font-semibold underline">Yêu cầu liên kết mới</Link></Alert>}
          <form onSubmit={onSubmit} noValidate className="space-y-4">
            <PasswordField label="Mật khẩu mới" autoComplete="new-password" showRules value={password} autoFocus error={errors.new_password?.message} {...register('new_password')} />
            <PasswordField label="Nhập lại mật khẩu mới" autoComplete="new-password" error={errors.confirm?.message} {...register('confirm')} />
            <Button type="submit" loading={isSubmitting}>Đổi mật khẩu</Button>
          </form>
        </>
      )}
    </AuthLayout>
  )
}
