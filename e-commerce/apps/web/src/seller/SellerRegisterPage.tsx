import { zodResolver } from '@hookform/resolvers/zod'
import { useCallback, useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { Navigate } from 'react-router-dom'
import { ApiError, api, type Province, type SellerApplication } from '../shared/api/client'
import { useAuth } from '../shared/auth/AuthContext'
import { Alert, Button, SelectField, Spinner, TextField } from '../shared/auth/components/ui'
import { describeError } from '../shared/auth/errors'
import { shopSchema, type ShopValues } from '../shared/auth/schemas'
import { AppShell } from '../shared/layout/AppShell'

/** Đăng ký người bán: nộp hồ sơ (cần email đã xác minh) rồi chờ admin duyệt. */
export default function SellerRegisterPage() {
  const { user, refreshUser } = useAuth()
  const [provinces, setProvinces] = useState<Province[] | null>(null)
  const [application, setApplication] = useState<SellerApplication | null | undefined>(undefined) // undefined: đang tải
  const [formError, setFormError] = useState<string>()

  const loadApplication = useCallback(async () => {
    try { setApplication(await api.myApplication()) } catch (e) {
      if (e instanceof ApiError && e.status === 404) setApplication(null)
      else { setApplication(null); setFormError(describeError(e).message) }
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    api.provinces().then(
      (p) => { if (!cancelled) setProvinces(p) },
      () => { if (!cancelled) { setProvinces([]); setFormError('Không tải được danh sách tỉnh/thành. Vui lòng tải lại trang.') } },
    )
    void loadApplication()
    return () => { cancelled = true }
  }, [loadApplication])

  // Hồ sơ đã được duyệt trong lúc đang mở trang: tải lại hồ sơ người dùng để role thành seller.
  useEffect(() => {
    if (application?.status === 'approved' && user?.role === 'buyer') void refreshUser()
  }, [application?.status, user?.role, refreshUser])

  const { register, handleSubmit, setError, formState: { errors, isSubmitting } } = useForm<ShopValues>({
    resolver: zodResolver(shopSchema),
    defaultValues: { name: '', province_code: '' },
  })

  if (user?.role === 'seller') return <Navigate to="/seller" replace />
  if (user?.role === 'admin') return <Navigate to="/admin" replace />

  const onSubmit = handleSubmit(async (v) => {
    setFormError(undefined)
    try {
      setApplication(await api.applySeller(v))
    } catch (e) {
      const d = describeError(e)
      d.fields.forEach((f) => ['name', 'province_code'].includes(f.field) && setError(f.field as keyof ShopValues, { message: f.message }))
      setFormError(d.message)
    }
  })

  const pending = application?.status === 'pending'
  const needsVerification = !user?.email_verified

  return (
    <AppShell width="max-w-md">
      <h1 className="text-2xl font-bold tracking-tight">Đăng ký bán hàng</h1>
      <p className="mt-1.5 text-sm text-zinc-500">Nộp hồ sơ mở shop. Quản trị viên sẽ xem xét và thông báo kết quả qua email.</p>
      <div className="mt-7 space-y-5 rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
        {formError && <Alert>{formError}</Alert>}
        {application === undefined || provinces === null ? (
          <Spinner label="Đang tải…" />
        ) : pending ? (
          <div role="status" aria-label="Hồ sơ đang chờ duyệt" className="space-y-2">
            <p className="inline-block rounded-full bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-800 dark:bg-amber-950/40 dark:text-amber-200">Đang chờ duyệt</p>
            <p className="font-semibold">{application.shop_name}</p>
            <p className="text-sm text-zinc-500">{application.province_name} · nộp ngày {new Date(application.created_at).toLocaleDateString('vi-VN')}</p>
            <p className="text-sm text-zinc-500">Bạn sẽ nhận email khi hồ sơ được xử lý.</p>
          </div>
        ) : (
          <>
            {application?.status === 'rejected' && (
              <Alert>Hồ sơ "{application.shop_name}" chưa được duyệt. Lý do: {application.reject_reason}. Bạn có thể chỉnh sửa và nộp lại.</Alert>
            )}
            {needsVerification && <Alert tone="info">Bạn cần xác minh email trước khi nộp hồ sơ. Dùng nút “Gửi lại email xác minh” ở đầu trang.</Alert>}
            <form onSubmit={onSubmit} noValidate className="space-y-4">
              <TextField label="Tên shop" placeholder="Cửa hàng của An" autoFocus error={errors.name?.message} {...register('name')} />
              <SelectField
                label="Tỉnh/thành (nơi bán)"
                placeholder="Chọn tỉnh/thành"
                options={provinces.map((p) => ({ value: p.code, label: p.name }))}
                error={errors.province_code?.message}
                {...register('province_code')}
              />
              <Button type="submit" loading={isSubmitting} disabled={needsVerification}>Gửi hồ sơ</Button>
            </form>
          </>
        )}
      </div>
    </AppShell>
  )
}
