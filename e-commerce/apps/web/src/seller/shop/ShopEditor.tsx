import { zodResolver } from '@hookform/resolvers/zod'
import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { api, type Province, type Shop } from '../../shared/api/client'
import { Alert, Button, SelectField, Spinner, TextField } from '../../shared/auth/components/ui'
import { describeError } from '../../shared/auth/errors'
import { shopSchema, type ShopValues } from '../../shared/auth/schemas'

const secondary = 'min-h-11 rounded-xl border border-zinc-300 px-4 text-sm font-medium hover:bg-zinc-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-500 disabled:opacity-50 dark:border-zinc-700 dark:hover:bg-zinc-800'

export function ShopEditor({ shop, onSaved, onCancel }: { shop: Shop; onSaved: (shop: Shop) => void; onCancel: () => void }) {
  const [provinces, setProvinces] = useState<Province[]>()
  const [loadError, setLoadError] = useState<string>()
  const [attempt, setAttempt] = useState(0)
  const { register, handleSubmit, setError, formState: { errors, isSubmitting } } = useForm<ShopValues>({
    resolver: zodResolver(shopSchema),
    defaultValues: { name: shop.name, province_code: shop.province.code },
  })

  useEffect(() => {
    let cancelled = false
    api.provinces().then(
      (data) => { if (!cancelled) setProvinces(data) },
      (error) => { if (!cancelled) setLoadError(describeError(error).message ?? 'Không tải được tỉnh/thành.') },
    )
    return () => { cancelled = true }
  }, [attempt])

  const save = handleSubmit(async (values) => {
    try {
      onSaved(await api.updateMyShop(values))
    } catch (error) {
      const details = describeError(error)
      const fields = details.fields.filter(({ field }) => field === 'name' || field === 'province_code')
      for (const { field, message } of fields) {
        setError(field as keyof ShopValues, { message })
      }
      if (details.message || !fields.length) {
        setError('root', { message: details.message ?? 'Không lưu được thông tin gian hàng.' })
      }
    }
  })

  return (
    <div className="mt-5 border-t border-zinc-200 pt-5 dark:border-zinc-800">
      <h3 className="mb-4 text-base font-semibold">Chỉnh sửa thông tin shop</h3>
      {loadError ? (
        <div className="space-y-4">
          <Alert>{loadError}</Alert>
          <div className="flex flex-wrap gap-2">
            <button type="button" className={secondary} onClick={onCancel}>Hủy chỉnh sửa</button>
            <button type="button" className={secondary} onClick={() => { setLoadError(undefined); setAttempt((value) => value + 1) }}>Tải lại tỉnh/thành</button>
          </div>
        </div>
      ) : !provinces ? (
        <div className="flex flex-wrap items-center justify-between gap-3">
          <Spinner label="Đang tải tỉnh/thành…" />
          <button type="button" className={secondary} onClick={onCancel}>Hủy chỉnh sửa</button>
        </div>
      ) : (
        <form aria-label="Chỉnh sửa thông tin shop" noValidate onSubmit={save} className="space-y-4">
          {errors.root?.message && <Alert>{errors.root.message}</Alert>}
          <div className="grid gap-4 sm:grid-cols-2">
            <TextField label="Tên shop" autoFocus maxLength={150} error={errors.name?.message} {...register('name')} />
            <SelectField
              label="Tỉnh/thành (nơi bán)"
              placeholder="Chọn tỉnh/thành"
              options={provinces.map((province) => ({ value: province.code, label: province.name }))}
              error={errors.province_code?.message}
              {...register('province_code')}
            />
          </div>
          <div className="flex flex-wrap justify-end gap-2">
            <button type="button" className={secondary} disabled={isSubmitting} onClick={onCancel}>Hủy chỉnh sửa</button>
            <div className="w-fit"><Button type="submit" loading={isSubmitting}>Lưu thay đổi</Button></div>
          </div>
        </form>
      )}
    </div>
  )
}
