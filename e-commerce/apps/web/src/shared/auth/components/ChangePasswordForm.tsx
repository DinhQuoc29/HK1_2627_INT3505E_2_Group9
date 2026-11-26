import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm, useWatch } from 'react-hook-form'
import { api } from '../../api/client'
import { useAuth } from '../AuthContext'
import { describeError } from '../errors'
import { changePasswordSchema, type ChangePasswordValues } from '../schemas'
import { Alert, Button, PasswordField } from './ui'

/** Đổi mật khẩu; tài khoản chỉ đăng nhập social thì đặt mật khẩu lần đầu (không cần mật khẩu cũ). */
export function ChangePasswordForm({ embedded = false }: { embedded?: boolean }) {
  const { user, refreshUser } = useAuth()
  const [message, setMessage] = useState<{ tone: 'error' | 'success'; text: string }>()
  const hasPassword = user?.has_password ?? true
  const { register, handleSubmit, setError, reset, control, formState: { errors, isSubmitting } } = useForm<ChangePasswordValues>({
    resolver: zodResolver(changePasswordSchema),
    defaultValues: { current_password: '', new_password: '', confirm: '' },
  })
  const newPassword = useWatch({ control, name: 'new_password' })
  const Heading = embedded ? 'h3' : 'h2'
  const field = embedded ? 'min-w-0 [&_input]:rounded-md' : undefined

  const onSubmit = handleSubmit(async ({ current_password, new_password }) => {
    setMessage(undefined)
    if (hasPassword && !current_password) {
      setError('current_password', { message: 'Vui lòng nhập mật khẩu hiện tại' })
      return
    }
    try {
      await api.changePassword({ ...(hasPassword ? { current_password } : {}), new_password })
      await refreshUser()
      reset()
      setMessage({ tone: 'success', text: hasPassword ? 'Đã đổi mật khẩu. Các thiết bị khác đã bị đăng xuất.' : 'Đã đặt mật khẩu.' })
    } catch (e) {
      const d = describeError(e)
      d.fields.forEach((f) => ['current_password', 'new_password'].includes(f.field) && setError(f.field as keyof ChangePasswordValues, { message: f.message }))
      setMessage({ tone: 'error', text: d.message ?? 'Không đổi được mật khẩu. Vui lòng kiểm tra lại các trường bên dưới.' })
    }
  })

  return (
    <section aria-labelledby="change-password" className={embedded
      ? 'rounded-md border border-slate-200 bg-slate-50 p-3.5 sm:p-4'
      : 'rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-900'}>
      <Heading id="change-password" className={embedded ? 'text-sm font-semibold' : 'text-lg font-semibold tracking-tight'}>{hasPassword ? 'Đổi mật khẩu' : 'Đặt mật khẩu'}</Heading>
      <p className={embedded ? 'mt-0.5 text-[13px] text-slate-600' : 'text-sm text-zinc-500'}>{hasPassword ? 'Sau khi đổi, các thiết bị khác sẽ bị đăng xuất.' : 'Thêm mật khẩu để có thể đăng nhập bằng email.'}</p>
      {message && <div className="mt-4"><Alert tone={message.tone}>{message.text}</Alert></div>}
      <form onSubmit={onSubmit} noValidate className="mt-4 max-w-sm space-y-4">
        {hasPassword && <PasswordField className={field} label="Mật khẩu hiện tại" autoComplete="current-password" error={errors.current_password?.message} {...register('current_password')} />}
        <PasswordField className={field} label="Mật khẩu mới" autoComplete="new-password" showRules value={newPassword} error={errors.new_password?.message} {...register('new_password')} />
        <PasswordField className={field} label="Nhập lại mật khẩu mới" autoComplete="new-password" error={errors.confirm?.message} {...register('confirm')} />
        <Button type="submit" loading={isSubmitting} className={embedded ? 'rounded-md bg-(--seller-accent) shadow-xs hover:bg-[#D94325] sm:w-auto' : undefined}>{hasPassword ? 'Đổi mật khẩu' : 'Đặt mật khẩu'}</Button>
      </form>
    </section>
  )
}
