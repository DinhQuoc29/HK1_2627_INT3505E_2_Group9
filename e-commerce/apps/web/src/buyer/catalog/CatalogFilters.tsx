import { useEffect, useState, type FormEvent } from 'react'
import { useLocation } from 'react-router-dom'
import { api } from '../../shared/api/client'
import { Alert, Spinner } from '../../shared/auth/components/ui'
import { StoreIcon } from '../../shared/layout/StoreIcon'
import { BuyerRequestError } from '../BuyerFeedback'
import { buyerErrorMessage, useBuyerRequest } from '../useBuyerRequest'

export const catalogFilterKeys = ['category', 'min_price', 'max_price', 'brand', 'province_code', 'sort'] as const

const preferredCategories = ['giay-dep', 'trang-tri-nha-cua', 'tui-va-phu-kien', 'thoi-trang']
const sortOptions = [
  { value: 'newest', label: 'Mới nhất' },
  { value: 'price-asc', label: 'Giá thấp đến cao' },
  { value: 'price-desc', label: 'Giá cao đến thấp' },
]

const inputClass = 'h-10 w-full min-w-0 rounded-lg bg-(--store-soft) px-3 text-base placeholder:text-(--store-muted) focus:bg-(--store-soft-hover) focus-visible:outline-2 focus-visible:outline-(--store-primary) sm:text-sm'
const applyClass = 'min-h-10 w-full cursor-pointer rounded-lg bg-linear-to-br from-(--store-primary-hover) to-(--store-primary) px-3 py-2 text-sm font-semibold text-white shadow-xs transition hover:shadow-md'
const textButtonClass = 'inline-flex min-h-8 cursor-pointer items-center rounded-sm text-xs font-semibold text-(--store-primary) hover:underline'

type ApplyFilters = (update: (next: URLSearchParams) => void) => void

export function CatalogFilters({ params, apply }: { params: URLSearchParams; apply: ApplyFilters }) {
  const location = useLocation()
  const [expanded, setExpanded] = useState(location.hash === '#catalog-filters')
  const [showAllCategories, setShowAllCategories] = useState(false)
  const categories = useBuyerRequest(api.catalogCategories)
  const selected = new Set(params.getAll('category').filter(Boolean))
  const groups = categories.state.status === 'ready' ? categories.state.data : []
  const names = new Map(groups.flatMap((group) => [group, ...group.children]).map(({ slug, name }) => [slug, name]))
  const primary = preferredCategories.filter((slug) => names.has(slug))
  const slugs = [...new Set([...primary, ...names.keys(), ...selected])]
  const visibleCategories = slugs.filter((slug, index) => showAllCategories || index < preferredCategories.length || selected.has(slug))
  const min = params.get('min_price') ?? ''
  const max = params.get('max_price') ?? ''
  const brand = params.get('brand') ?? ''
  const province = params.get('province_code') ?? ''
  const hasQuery = Boolean(params.get('q')?.trim())
  const sort = params.get('sort') ?? (hasQuery ? '' : 'newest')
  const sorting = hasQuery ? [{ value: '', label: 'Phù hợp nhất' }, ...sortOptions] : sortOptions

  useEffect(() => {
    if (location.hash === '#catalog-filters') setExpanded(true)
  }, [location.hash, location.key])

  function toggleCategory(slug: string) {
    apply((next) => {
      if (selected.has(slug)) next.delete('category', slug)
      else next.append('category', slug)
    })
  }

  function changeSort(value: string) {
    apply((next) => {
      if (!value || (value === 'newest' && !hasQuery)) next.delete('sort')
      else next.set('sort', value)
    })
  }

  return (
    <aside id="catalog-filters" aria-labelledby="catalog-filters-title" className="min-w-0 self-start scroll-mt-32 rounded-xl bg-white p-4 shadow-xs md:scroll-mt-44 lg:sticky lg:top-24 lg:max-h-[calc(100dvh-7rem)] lg:overflow-y-auto lg:scroll-mt-52 lg:p-6">
      <div className="flex flex-wrap items-center justify-between gap-x-3">
        <div className="flex items-center gap-2">
          <StoreIcon name="tune" className="size-5 text-(--store-primary)" />
          <h2 id="catalog-filters-title" className="text-base font-semibold">Bộ lọc</h2>
        </div>
        {visibleCategories.length > 0 && <span className="hidden text-xs text-(--store-muted) lg:inline">{visibleCategories.length} mục</span>}
        <button type="button" className={`${textButtonClass} lg:hidden`} aria-expanded={expanded} aria-controls="catalog-filter-options" onClick={() => setExpanded((open) => !open)}>
          {expanded ? 'Ẩn bộ lọc' : 'Mở bộ lọc'}
        </button>
      </div>

      <div id="catalog-filter-options" className={`${expanded ? 'block' : 'hidden'} mt-5 space-y-7 lg:block lg:mt-6`}>
        <fieldset>
          <legend className="mb-2 text-sm font-semibold">Danh mục</legend>
          <div className="space-y-1" id="catalog-category-options">
            {visibleCategories.map((slug) => (
              <FilterOption key={slug} label={names.get(slug) ?? slug} checked={selected.has(slug)} change={() => toggleCategory(slug)} />
            ))}
          </div>
          {categories.state.status === 'loading' && <Spinner label="Đang tải danh mục…" />}
          {categories.state.status === 'error' && <BuyerRequestError message="Không tải được danh mục." retry={categories.retry} />}
          {categories.state.status === 'ready' && slugs.length === 0 && <p className="text-xs text-(--store-muted)">Chưa có danh mục</p>}
          {slugs.length > preferredCategories.length && (
            <button type="button" className={`${textButtonClass} ml-2`} aria-expanded={showAllCategories} aria-controls="catalog-category-options" onClick={() => setShowAllCategories((show) => !show)}>
              {showAllCategories ? 'Thu gọn danh mục' : 'Xem thêm danh mục'}
            </button>
          )}
        </fieldset>

        <PriceFilter key={JSON.stringify([min, max])} min={min} max={max} apply={apply} />

        <fieldset>
          <legend className="mb-2 text-sm font-semibold">Sắp xếp</legend>
          <div className="space-y-1">
            {sorting.map(({ value, label }) => (
              <FilterOption key={value} label={label} value={value} checked={sort === value} change={() => changeSort(value)} radio />
            ))}
          </div>
        </fieldset>

        <details open={Boolean(brand || province)} className="border-t border-(--store-outline) pt-3">
          <summary className="cursor-pointer rounded-sm py-1 text-sm font-semibold hover:text-(--store-primary)">Bộ lọc khác</summary>
          <ShopFilter key={JSON.stringify([brand, province])} brand={brand} province={province} apply={apply} />
        </details>
      </div>
    </aside>
  )
}

function FilterOption({ label, checked, change, radio = false, value }: { label: string; checked: boolean; change: () => void; radio?: boolean; value?: string }) {
  return (
    <label className="relative flex min-h-8 cursor-pointer items-center gap-2 rounded-lg px-2 py-1.5 text-sm text-(--store-muted) hover:bg-(--store-soft)">
      <input type={radio ? 'radio' : 'checkbox'} name={radio ? 'catalog-sort' : undefined} value={value} checked={checked} onChange={change} className="peer absolute inset-0 size-full cursor-pointer opacity-0" />
      <span aria-hidden="true" className={`grid size-[18px] shrink-0 place-items-center bg-(--store-soft) text-transparent transition-colors peer-checked:bg-(--store-primary) peer-checked:text-white peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-(--store-primary) ${radio ? 'rounded-full' : 'rounded'}`}>
        {radio ? <span className="size-2 rounded-full bg-current" /> : <StoreIcon name="check" className="size-3.5" />}
      </span>
      <span className="wrap-anywhere peer-checked:font-semibold peer-checked:text-(--store-ink)">{label}</span>
    </label>
  )
}

function PriceFilter({ min, max, apply }: { min: string; max: string; apply: ApplyFilters }) {
  const [error, setError] = useState('')

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const fields = new FormData(event.currentTarget)
    const lower = String(fields.get('min_price') ?? '')
    const upper = String(fields.get('max_price') ?? '')
    if (lower && upper && Number(lower) > Number(upper)) {
      setError('Giá tối đa phải lớn hơn hoặc bằng giá tối thiểu.')
      return
    }
    setError('')
    apply((next) => {
      if (lower) next.set('min_price', String(Number(lower)))
      else next.delete('min_price')
      if (upper) next.set('max_price', String(Number(upper)))
      else next.delete('max_price')
    })
  }

  return (
    <form onSubmit={submit}>
      <fieldset className="space-y-3">
        <legend className="mb-2 text-sm font-semibold">Khoảng giá</legend>
        <div className="grid grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] items-center gap-2">
          <input aria-label="Giá từ" aria-invalid={Boolean(error)} name="min_price" type="number" inputMode="numeric" min={0} max={Number.MAX_SAFE_INTEGER} step={1} placeholder="Từ ₫" defaultValue={min} className={inputClass} />
          <span aria-hidden="true" className="text-sm text-(--store-muted)">–</span>
          <input aria-label="Giá đến" aria-invalid={Boolean(error)} name="max_price" type="number" inputMode="numeric" min={0} max={Number.MAX_SAFE_INTEGER} step={1} placeholder="Đến ₫" defaultValue={max} className={inputClass} />
        </div>
        {error && <Alert>{error}</Alert>}
        <button type="submit" className={applyClass}>Áp dụng</button>
      </fieldset>
    </form>
  )
}

function ShopFilter({ brand, province, apply }: { brand: string; province: string; apply: ApplyFilters }) {
  const provinces = useBuyerRequest(api.provinces)
  const [selectedProvince, setSelectedProvince] = useState(province)
  const places = provinces.state.status === 'ready' ? provinces.state.data : []

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const value = String(new FormData(event.currentTarget).get('brand') ?? '').trim()
    apply((next) => {
      if (value) next.set('brand', value)
      else next.delete('brand')
      if (selectedProvince) next.set('province_code', selectedProvince)
      else next.delete('province_code')
    })
  }

  return (
    <form onSubmit={submit} className="mt-2 space-y-3">
      <label className="block space-y-1 text-sm">
        <span>Thương hiệu</span>
        <input name="brand" maxLength={100} placeholder="Ví dụ: Samsung" defaultValue={brand} className={inputClass} />
      </label>
      <label className="block space-y-1 text-sm">
        <span>Tỉnh/thành của shop</span>
        <select name="province_code" value={selectedProvince} onChange={(event) => setSelectedProvince(event.target.value)} className={inputClass}>
          <option value="">Tất cả tỉnh/thành</option>
          {selectedProvince && !places.some(({ code }) => code === selectedProvince) && <option value={selectedProvince}>Mã tỉnh/thành {selectedProvince}</option>}
          {places.map(({ code, name }) => <option key={code} value={code}>{name}</option>)}
        </select>
      </label>
      {provinces.state.status === 'loading' && <Spinner label="Đang tải tỉnh/thành…" />}
      {provinces.state.status === 'error' && <BuyerRequestError message={buyerErrorMessage(provinces.state.error, 'Không tải được tỉnh/thành.')} retry={provinces.retry} />}
      <button type="submit" className={applyClass}>Áp dụng bộ lọc khác</button>
    </form>
  )
}
