import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link } from 'react-router-dom'
import { api } from '../../api/client'
import { AuthLayout } from '../components/AuthLayout'
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
    <AuthLayout
      title="Quên mật khẩu"
      subtitle="Nhập email đăng ký, chúng tôi sẽ gửi liên kết đặt lại mật khẩu."
      footer={<Link to="/login" className="font-semibold text-brand-600 hover:underline">Quay lại đăng nhập</Link>}
    >
      {sentTo ? (
        <Alert tone="success">
          Nếu <strong>{sentTo}</strong> đã đăng ký, một email hướng dẫn đặt lại mật khẩu đang được gửi tới. Liên kết có hiệu lực trong 60 phút.
        </Alert>
      ) : (
        <>
          {formError && <Alert>{formError}</Alert>}
          <form onSubmit={onSubmit} noValidate className="space-y-4">
            <TextField label="Email" type="email" autoComplete="email" inputMode="email" placeholder="ban@example.com" autoFocus error={errors.email?.message} {...register('email')} />
            <Button type="submit" loading={isSubmitting}>Gửi liên kết đặt lại</Button>
          </form>
        </>
      )}
    </AuthLayout>
  )
}
