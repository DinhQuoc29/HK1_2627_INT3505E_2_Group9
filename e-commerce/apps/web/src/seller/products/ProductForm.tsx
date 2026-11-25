import { zodResolver } from '@hookform/resolvers/zod'
import { useFieldArray, useForm } from 'react-hook-form'
import { z } from 'zod'
import { ApiError, type ProductCategory, type ProductInput, type SellerProduct } from '../../shared/api/client'
import { Alert, Button, SelectField, TextField } from '../../shared/auth/components/ui'

export function imageUrl(value: string): string | undefined {
  if (!/^https?:\/\//i.test(value) || /[\s\\]/.test(value)) return undefined
  try {
    const url = new URL(value)
    if (['https:', 'http:'].includes(url.protocol) && !url.username && !url.password) return url.href
  } catch {
    return undefined
  }
  return undefined
}

const wholeNumber = (label: string, min: number, max: number) => z.string().trim().refine(
  (value) => /^\d+$/.test(value) && Number(value) >= min && Number(value) <= max,
  `${label} phải là số nguyên từ ${min.toLocaleString('vi-VN')} đến ${max.toLocaleString('vi-VN')}.`,
)

const schema = z.object({
  name: z.string().trim().min(1, 'Nhập tên sản phẩm.').max(255, 'Tên sản phẩm tối đa 255 ký tự.'),
  brand: z.string().trim().max(100, 'Thương hiệu tối đa 100 ký tự.'),
  description: z.string().trim().min(1, 'Nhập mô tả sản phẩm.').max(5000, 'Mô tả tối đa 5.000 ký tự.'),
  category_id: z.string().min(1, 'Chọn danh mục sản phẩm.'),
  price: wholeNumber('Giá', 1, Number.MAX_SAFE_INTEGER),
  quantity: wholeNumber('Tồn kho', 0, 2_147_483_647),
  images: z.array(z.object({
    url: z.string().trim().max(500, 'Liên kết tối đa 500 ký tự.').refine(imageUrl, 'Nhập liên kết ảnh HTTP hoặc HTTPS hợp lệ.'),
  })).min(1).max(8),
})

type FormValues = z.infer<typeof schema>

function initialValues(product?: SellerProduct): FormValues {
  return {
    name: product?.name ?? '',
    brand: product?.brand ?? '',
    description: product?.description ?? '',
    category_id: product?.category_id ?? '',
    price: product ? String(product.price) : '',
    quantity: String(product?.quantity ?? 0),
    images: product?.images.length ? product.images.map((url) => ({ url })) : [{ url: '' }],
  }
}

export function ProductForm({ categories, product, onSave, onCancel }: {
  categories: ProductCategory[]
  product?: SellerProduct
  onSave: (input: ProductInput) => Promise<void>
  onCancel: () => void
}) {
  const { control, register, handleSubmit, watch, setError, formState: { errors, isSubmitting } } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: initialValues(product),
  })
  const { fields, append, remove, move } = useFieldArray({ control, name: 'images' })
  const images = watch('images')

  const submit = handleSubmit(async (values) => {
    try {
      await onSave({
        ...values,
        brand: values.brand || null,
        quantity: Number(values.quantity),
        price: Number(values.price),
        images: values.images.map(({ url }) => url),
      })
    } catch (error) {
      const fields = error instanceof ApiError ? error.errors : []
      for (const { field, message } of fields) {
        if (Object.hasOwn(schema.shape, field)) setError(field as keyof FormValues, { message })
      }
      setError('root', { message: error instanceof Error ? error.message : 'Không lưu được sản phẩm. Vui lòng thử lại.' })
    }
  })

  return (
    <form onSubmit={submit} noValidate className="space-y-5">
      {errors.root?.message && <Alert>{errors.root.message}</Alert>}
      {categories.length === 0 && <Alert tone="info">Chưa có danh mục sản phẩm. Hãy liên hệ quản trị viên để bổ sung danh mục.</Alert>}
      <div className="grid gap-4 sm:grid-cols-2">
        <TextField label="Tên sản phẩm" maxLength={255} error={errors.name?.message} {...register('name')} />
        <TextField label="Thương hiệu (không bắt buộc)" maxLength={100} error={errors.brand?.message} {...register('brand')} />
        <SelectField
          label="Danh mục"
          placeholder="Chọn danh mục"
          options={categories.map(({ id, name, parent_name }) => ({ value: id, label: `${parent_name} / ${name}` }))}
          error={errors.category_id?.message}
          {...register('category_id')}
        />
        <div className="grid grid-cols-2 gap-3">
          <TextField label="Giá (₫)" inputMode="numeric" error={errors.price?.message} {...register('price')} />
          <TextField label="Tồn kho" inputMode="numeric" error={errors.quantity?.message} {...register('quantity')} />
        </div>
      </div>
      <div>
        <label htmlFor="product-description" className="mb-1.5 block text-sm font-medium">Mô tả</label>
        <textarea
          id="product-description"
          rows={4}
          maxLength={5000}
          aria-invalid={!!errors.description}
          aria-describedby={errors.description ? 'product-description-error' : undefined}
          className="w-full rounded-xl border border-zinc-300 bg-white px-3.5 py-2.5 text-sm focus-visible:outline-2 focus-visible:outline-brand-500 dark:border-zinc-700 dark:bg-zinc-900"
          {...register('description')}
        />
        {errors.description && <p id="product-description-error" className="mt-1.5 text-xs text-red-700 dark:text-red-400">{errors.description.message}</p>}
      </div>

      <fieldset className="min-w-0 space-y-3 rounded-xl border border-zinc-200 p-3 sm:p-4 dark:border-zinc-800">
        <legend className="px-1 text-sm font-semibold">Hình ảnh</legend>
        <p className="text-sm text-zinc-600 dark:text-zinc-400">Thêm tối đa 8 liên kết ảnh. Ảnh đầu tiên là ảnh đại diện.</p>
        {errors.images?.message && <p className="text-sm text-red-700 dark:text-red-400">{errors.images.message}</p>}
        {fields.map((field, index) => {
          const preview = imageUrl(images[index]?.url ?? '')
          return (
            <div key={field.id} className="flex flex-wrap items-start gap-3 rounded-lg bg-zinc-50 p-3 dark:bg-zinc-800/60">
              {preview && <img src={preview} alt="" referrerPolicy="no-referrer" className="size-14 shrink-0 rounded-md object-cover" />}
              <div className="min-w-0 flex-1 basis-44">
                <TextField
                  label={index === 0 ? 'Liên kết ảnh đại diện' : `Liên kết ảnh ${index + 1}`}
                  type="url"
                  maxLength={500}
                  placeholder="https://…"
                  error={errors.images?.[index]?.url?.message}
                  {...register(`images.${index}.url`)}
                />
                <div className="mt-1.5 flex flex-wrap gap-2 text-sm">
                  {index > 0 && <button type="button" onClick={() => move(index, 0)} className="min-h-9 px-2 text-brand-700 underline underline-offset-4 dark:text-brand-100">Đặt làm ảnh đại diện</button>}
                  {fields.length > 1 && <button type="button" onClick={() => remove(index)} aria-label={`Gỡ ảnh ${index + 1}`} className="min-h-9 px-2 text-red-700 underline underline-offset-4 dark:text-red-300">Gỡ ảnh</button>}
                </div>
              </div>
            </div>
          )
        })}
        {fields.length < 8 && (
          <button type="button" onClick={() => append({ url: '' })} className="min-h-10 rounded-lg border border-zinc-300 px-3 text-sm font-medium dark:border-zinc-700">
            Thêm liên kết ảnh
          </button>
        )}
      </fieldset>

      <div className="grid gap-2 sm:grid-cols-[auto_minmax(0,14rem)] sm:justify-end">
        <button type="button" disabled={isSubmitting} onClick={onCancel} className="min-h-11 rounded-xl border border-zinc-300 px-4 text-sm font-medium dark:border-zinc-700">Hủy</button>
        <Button type="submit" loading={isSubmitting} disabled={!categories.length}>{product ? 'Lưu thay đổi' : 'Đăng sản phẩm'}</Button>
      </div>
    </form>
  )
}
