import { useState, type FormEvent } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { api, type CatalogCategoryGroup, type Province } from '../../shared/api/client'
import { Alert, SelectField, Spinner, TextField } from '../../shared/auth/components/ui'
import { buyerErrorMessage, useBuyerRequest } from '../useBuyerRequest'
import { BuyerRequestError, buyerLink } from '../BuyerFeedback'

const filterKeys = ['category', 'brand', 'province_code', 'min_price', 'max_price'] as const
type Filters = Record<(typeof filterKeys)[number], string>

export function CatalogFilters({ params, apply }: { params: URLSearchParams; apply: (next: URLSearchParams) => void }) {
  const { hash } = useLocation()
  const [expanded, setExpanded] = useState(hash === '#catalog-filters')
  const filters: Filters = {
    category: params.get('category') ?? '',
    brand: params.get('brand') ?? '',
    province_code: params.get('province_code') ?? '',
    min_price: params.get('min_price') ?? '',
    max_price: params.get('max_price') ?? '',
  }
  const categories = useBuyerRequest(api.catalogCategories)
  const provinces = useBuyerRequest(api.provinces)
  const activeCount = filterKeys.filter((key) => params.has(key)).length
  const query = params.get('q')
  const reset = query ? `/products?${new URLSearchParams({ q: query })}` : '/products'

  return (
    <aside id="catalog-filters" aria-labelledby="catalog-filters-title" className="min-w-0 self-start scroll-mt-32 rounded-2xl border border-zinc-200 bg-white px-3 py-2 sm:px-5 md:scroll-mt-24 lg:py-4 dark:border-zinc-800 dark:bg-zinc-900">
      <div className="flex flex-wrap items-center justify-between gap-x-2">
        <h2 id="catalog-filters-title" className="px-1 text-base font-bold lg:text-lg">
          Bộ lọc {activeCount > 0 && <span className="text-sm font-medium text-zinc-500">({activeCount})</span>}
        </h2>
        <div className="flex flex-wrap items-center">
          {activeCount > 0 && <Link to={reset} className={buyerLink}>Xóa bộ lọc</Link>}
          <button
            type="button"
            className={`${buyerLink} lg:hidden`}
            aria-expanded={expanded}
            aria-controls="catalog-filter-options"
            onClick={() => setExpanded((open) => !open)}
          >{expanded ? 'Ẩn tùy chọn' : 'Mở bộ lọc'}</button>
        </div>
      </div>
      <div id="catalog-filter-options" className={`${expanded ? 'block' : 'hidden'} pt-3 pb-2 lg:block`}>
        <FilterForm
          key={JSON.stringify(filters)}
          filters={filters}
          categories={categories}
          provinces={provinces}
          apply={(next) => {
            if (query) next.set('q', query)
            setExpanded(false)
            apply(next)
          }}
        />
      </div>
    </aside>
  )
}

function FilterForm({
  filters, categories, provinces, apply,
}: {
  filters: Filters
  categories: ReturnType<typeof useBuyerRequest<CatalogCategoryGroup[]>>
  provinces: ReturnType<typeof useBuyerRequest<Province[]>>
  apply: (next: URLSearchParams) => void
}) {
  const [error, setError] = useState('')
  const [category, setCategory] = useState(filters.category)
  const [provinceCode, setProvinceCode] = useState(filters.province_code)
  const groups = categories.state.status === 'ready' ? categories.state.data : []
  const places = provinces.state.status === 'ready' ? provinces.state.data : []
  const knownCategory = groups.some((group) => group.slug === category || group.children.some((child) => child.slug === category))
  const provinceOptions = places.map((place) => ({ label: place.name, value: place.code }))
  if (provinceCode && !places.some((place) => place.code === provinceCode)) {
    provinceOptions.unshift({ label: `Mã tỉnh/thành ${provinceCode}`, value: provinceCode })
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const data = new FormData(event.currentTarget)
    const next = new URLSearchParams()
    for (const key of filterKeys) {
      const value = String(data.get(key) ?? '').trim()
      if (!value) continue
      next.set(key, key === 'min_price' || key === 'max_price' ? String(Number(value)) : value)
    }
    const min = next.get('min_price')
    const max = next.get('max_price')
    if (min !== null && max !== null && Number(min) > Number(max)) {
      setError('Giá tối đa phải lớn hơn hoặc bằng giá tối thiểu.')
      return
    }
    setError('')
    apply(next)
  }

  return (
    <form onSubmit={submit} className="space-y-4">
      <div>
        <label htmlFor="catalog-category" className="mb-1.5 block text-sm font-medium">Danh mục</label>
        <select
          id="catalog-category"
          name="category"
          value={category}
          onChange={(event) => setCategory(event.target.value)}
          className="h-11 w-full rounded-xl border border-zinc-300 bg-white px-3 text-sm focus-visible:outline-brand-500 dark:border-zinc-700 dark:bg-zinc-900"
        >
          <option value="">Tất cả danh mục</option>
          {category && !knownCategory && <option value={category}>{category}</option>}
          {groups.map((group) => (
            <optgroup key={group.slug} label={group.name}>
              <option value={group.slug}>Tất cả trong {group.name}</option>
              {group.children.map((child) => <option key={child.slug} value={child.slug}>{child.name}</option>)}
            </optgroup>
          ))}
        </select>
        {categories.state.status === 'loading' && <Spinner label="Đang tải danh mục…" />}
        {categories.state.status === 'error' && <BuyerRequestError message="Không tải được danh mục." retry={categories.retry} />}
      </div>

      <fieldset>
        <legend className="mb-2 text-sm font-medium">Khoảng giá (₫)</legend>
        <div className="grid grid-cols-2 gap-2">
          <TextField label="Từ" name="min_price" type="number" min={0} max={Number.MAX_SAFE_INTEGER} step={1} defaultValue={filters.min_price} />
          <TextField label="Đến" name="max_price" type="number" min={0} max={Number.MAX_SAFE_INTEGER} step={1} defaultValue={filters.max_price} />
        </div>
      </fieldset>

      <TextField label="Thương hiệu" name="brand" placeholder="Ví dụ: Samsung" maxLength={100} defaultValue={filters.brand} />
      <div>
        <SelectField
          label="Tỉnh/thành của shop"
          name="province_code"
          placeholder="Tất cả tỉnh/thành"
          options={provinceOptions}
          value={provinceCode}
          onChange={(event) => setProvinceCode(event.target.value)}
        />
        {provinces.state.status === 'loading' && <Spinner label="Đang tải tỉnh/thành…" />}
        {provinces.state.status === 'error' && (
          <BuyerRequestError message={buyerErrorMessage(provinces.state.error, 'Không tải được tỉnh/thành.')} retry={provinces.retry} />
        )}
      </div>
      {error && <Alert>{error}</Alert>}
      <button type="submit" className="min-h-11 w-full rounded-xl bg-brand-600 px-4 text-sm font-semibold text-white hover:bg-brand-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-500">
        Áp dụng bộ lọc
      </button>
    </form>
  )
}
