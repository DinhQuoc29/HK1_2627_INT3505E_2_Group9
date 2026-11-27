import { useEffect, useState } from 'react'
import { api, type ProductCategory, type ProductInput, type ProductStatus, type SellerProduct, type SellerProductPage } from '../../shared/api/client'
import { Alert, Spinner } from '../../shared/auth/components/ui'
import { describeError } from '../../shared/auth/errors'
import { AppShell } from '../../shared/layout/AppShell'
import { SellerIcon } from '../sellerUi'
import { ProductForm } from './ProductForm'
import { isLowStock, SellerProductTable } from './SellerProductTable'

type Editor = { mode: 'create' } | { mode: 'edit'; product: SellerProduct }
type Sort = 'newest' | 'name' | 'price-asc' | 'price-desc'

const panel = 'min-w-0 rounded-lg border border-slate-200 bg-white shadow-xs'
const focus = 'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-(--seller-accent)'
const control = `min-h-11 min-w-0 rounded-md border border-slate-200 bg-white px-3 text-[13px] text-slate-700 sm:min-h-9 ${focus}`
const secondary = `min-h-10 rounded-md border border-slate-200 px-3 text-[13px] font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50 ${focus}`
const number = new Intl.NumberFormat('vi-VN')
const nameOrder = new Intl.Collator('vi-VN')

function ProductSummary({ items, pageOnly }: { items: SellerProduct[]; pageOnly: boolean }) {
  const active = items.filter(({ status }) => status === 'active').length
  const stock = items.reduce((total, { quantity }) => total + quantity, 0)
  const low = items.filter(({ quantity }) => isLowStock(quantity)).length
  const chip = 'flex items-center gap-1.5 rounded-md border border-slate-200 bg-white px-3 py-1.5 shadow-xs'

  return (
    <dl aria-label={pageOnly ? 'Thống kê sản phẩm trên trang này' : 'Thống kê sản phẩm của gian hàng'} className="flex flex-wrap items-center gap-2 text-[13px] text-slate-500">
      {pageOnly && <div className="text-xs font-medium"><dt className="sr-only">Phạm vi</dt><dd>Trang này</dd></div>}
      <div className={chip}>
        <dt>Tổng sản phẩm:</dt><dd className="font-semibold text-slate-800">{number.format(items.length)}</dd>
      </div>
      <div className={chip}>
        <dt className="flex items-center gap-1.5"><span aria-hidden="true" className="size-2 rounded-full bg-emerald-500" />Đang hiển thị:</dt>
        <dd className="font-semibold text-slate-800">{number.format(active)}</dd>
      </div>
      <div className={chip}>
        <dt>Tổng tồn kho:</dt><dd className="font-semibold text-slate-800">{number.format(stock)}</dd>
      </div>
      <div className={chip} title="Sản phẩm còn từ 1 đến 5 đơn vị">
        <dt className="flex items-center gap-1.5"><span aria-hidden="true" className="size-2 rounded-full bg-amber-500" />Cảnh báo sắp hết:</dt>
        <dd className="font-semibold text-amber-700">{number.format(low)}</dd>
      </div>
    </dl>
  )
}

export default function SellerProductsPage() {
  const [filter, setFilter] = useState<{ q: string; status: ProductStatus | ''; page: number }>({ q: '', status: '', page: 1 })
  const [search, setSearch] = useState('')
  const [sort, setSort] = useState<Sort>('newest')
  const [result, setResult] = useState<SellerProductPage>()
  const [loading, setLoading] = useState(true)
  const [listError, setListError] = useState<string>()
  const [actionError, setActionError] = useState<string>()
  const [notice, setNotice] = useState<string>()
  const [changing, setChanging] = useState(false)
  const [refresh, setRefresh] = useState(0)
  const [editor, setEditor] = useState<Editor | null>(null)
  const [categories, setCategories] = useState<ProductCategory[]>()
  const [categoryError, setCategoryError] = useState<string>()
  const [categoryAttempt, setCategoryAttempt] = useState(0)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setListError(undefined)
    api.sellerProducts(filter).then(
      (data) => { if (!cancelled) { setResult(data); setLoading(false) } },
      (error) => {
        if (cancelled) return
        setResult(undefined)
        setListError(describeError(error).message ?? 'Không tải được sản phẩm.')
        setLoading(false)
      },
    )
    return () => { cancelled = true }
  }, [filter, refresh])

  useEffect(() => {
    if (!editor) return
    let cancelled = false
    setCategories(undefined)
    setCategoryError(undefined)
    api.sellerProductCategories().then(
      (data) => { if (!cancelled) setCategories(data) },
      (error) => { if (!cancelled) setCategoryError(describeError(error).message ?? 'Không tải được danh mục.') },
    )
    return () => { cancelled = true }
  }, [editor, categoryAttempt])

  const openEditor = (next: Editor) => {
    setCategories(undefined)
    setCategoryError(undefined)
    setActionError(undefined)
    setNotice(undefined)
    setEditor(next)
  }

  const save = async (product: ProductInput) => {
    if (editor?.mode === 'edit') {
      await api.updateSellerProduct(editor.product.id, product)
      setNotice('Đã lưu thay đổi sản phẩm.')
    } else {
      await api.addSellerProduct(product)
      setSearch('')
      setFilter({ q: '', status: '', page: 1 })
      setNotice('Đã đăng sản phẩm.')
    }
    setEditor(null)
    setRefresh((count) => count + 1)
  }

  const changeVisibility = async (products: SellerProduct[], nextStatus: ProductStatus) => {
    const targets = products.filter(({ status }) => status !== nextStatus)
    if (!targets.length || changing) return
    setChanging(true)
    setActionError(undefined)
    setNotice(undefined)
    try {
      let saved = 0
      let firstError: string | undefined
      for (const product of targets) {
        try {
          await api.changeSellerProductStatus(product.id, nextStatus)
          saved++
        } catch (error) {
          firstError ??= describeError(error).message ?? 'Không cập nhật được trạng thái sản phẩm.'
        }
      }
      if (saved > 0) {
        const action = nextStatus === 'active' ? 'Đã hiển thị lại' : 'Đã ẩn'
        setNotice(targets.length === 1 ? `${action} sản phẩm.` : `${action} ${number.format(saved)} sản phẩm.`)
        setLoading(true)
        setRefresh((count) => count + 1)
      }
      if (firstError) {
        setActionError(targets.length === 1 ? firstError : `Chưa cập nhật được ${number.format(targets.length - saved)} sản phẩm. ${firstError}`)
      }
    } finally {
      setChanging(false)
    }
  }

  const filtered = Boolean(filter.q || filter.status)
  const multiplePages = filter.page > 1 || Boolean(result?.has_more)
  const currentItems = result?.items ?? []
  const items = sort === 'newest' ? currentItems : [...currentItems].sort((a, b) => {
    if (sort === 'name') return nameOrder.compare(a.name, b.name)
    return sort === 'price-asc' ? a.price - b.price : b.price - a.price
  })

  return (
    <AppShell>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-[22px] leading-7 font-semibold tracking-tight">{editor ? (editor.mode === 'create' ? 'Thêm sản phẩm' : 'Sửa sản phẩm') : 'Quản lý sản phẩm'}</h1>
            {!editor && !loading && result && !filtered && !multiplePages && (
              <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600">{number.format(items.length)} sản phẩm</span>
            )}
          </div>
          <p className="mt-0.5 text-[13px] leading-5 text-slate-500">{editor ? 'Cập nhật thông tin, ảnh và số lượng tồn kho.' : 'Quản lý sản phẩm và tình trạng hiển thị trong gian hàng.'}</p>
        </div>
        {!editor && (
          <button type="button" className={`inline-flex min-h-11 items-center gap-1.5 rounded-md bg-(--seller-accent) px-3.5 text-[13px] font-semibold text-white shadow-xs transition-colors hover:bg-[#D94325] disabled:opacity-50 sm:min-h-9 ${focus}`} disabled={changing} onClick={() => openEditor({ mode: 'create' })}>
            <SellerIcon name="add" />
            Thêm sản phẩm
          </button>
        )}
      </div>

      {editor ? (
        <section aria-label="Thông tin sản phẩm" className={`${panel} p-4 sm:p-5`}>
          {categoryError ? (
            <div className="space-y-4">
              <Alert>{categoryError}</Alert>
              <div className="flex flex-wrap gap-2">
                <button type="button" className={secondary} onClick={() => setEditor(null)}>Quay lại</button>
                <button type="button" className={secondary} onClick={() => setCategoryAttempt((count) => count + 1)}>Thử lại</button>
              </div>
            </div>
          ) : categories ? (
            <ProductForm
              categories={categories}
              product={editor.mode === 'edit' ? editor.product : undefined}
              onSave={save}
              onCancel={() => setEditor(null)}
            />
          ) : (
            <div className="flex flex-wrap items-center justify-between gap-3">
              <Spinner label="Đang tải danh mục…" />
              <button type="button" className={secondary} onClick={() => setEditor(null)}>Quay lại</button>
            </div>
          )}
        </section>
      ) : (
        <div className="space-y-4">
          {!loading && result && <ProductSummary items={items} pageOnly={filtered || multiplePages} />}
          <form
            aria-label="Tìm và lọc sản phẩm"
            className={`flex flex-wrap items-center justify-between gap-3 p-3 ${panel}`}
            onSubmit={(event) => { event.preventDefault(); setFilter((current) => ({ ...current, q: search.trim(), page: 1 })) }}
          >
            <div className="grid min-w-0 flex-1 basis-[30rem] grid-cols-[minmax(0,1fr)_auto] gap-2 sm:grid-cols-[minmax(0,1fr)_auto_auto]">
              <div className="relative col-span-2 min-w-0 sm:col-span-1">
                <SellerIcon name="search" className="pointer-events-none absolute top-1/2 left-3 size-[18px] -translate-y-1/2 text-slate-400" />
                <input type="search" className={`${control} w-full pl-9 text-slate-900 placeholder:text-slate-400`} aria-label="Tìm theo tên sản phẩm" placeholder="Tìm theo tên sản phẩm…" maxLength={255} value={search} onChange={(event) => setSearch(event.target.value)} />
              </div>
              <select className={control} aria-label="Lọc theo trạng thái" disabled={changing} value={filter.status} onChange={(event) => setFilter((current) => ({ ...current, status: event.target.value as ProductStatus | '', page: 1 }))}>
                <option value="">Mọi trạng thái</option>
                <option value="active">Đang hiển thị</option>
                <option value="inactive">Đã ẩn</option>
              </select>
              <button type="submit" disabled={changing} className={`min-h-11 rounded-md bg-slate-900 px-3.5 text-[13px] font-medium whitespace-nowrap text-white shadow-xs transition-colors hover:bg-slate-800 disabled:opacity-50 sm:min-h-9 ${focus}`}>Tìm kiếm</button>
            </div>
            <label className="flex min-w-0 items-center gap-1.5 text-xs whitespace-nowrap text-slate-500">
              <SellerIcon name="sort" className="size-4" />
              <span>{multiplePages ? 'Sắp xếp trang này:' : 'Sắp xếp:'}</span>
              <select aria-label={multiplePages ? 'Sắp xếp sản phẩm trên trang này' : 'Sắp xếp sản phẩm'} className={`min-h-10 min-w-0 rounded-md px-1.5 text-xs font-medium text-slate-800 sm:min-h-9 ${focus}`} value={sort} onChange={(event) => setSort(event.target.value as Sort)}>
                <option value="newest">Mới nhất</option>
                <option value="name">Tên A–Z</option>
                <option value="price-asc">Giá tăng dần</option>
                <option value="price-desc">Giá giảm dần</option>
              </select>
            </label>
          </form>
          {notice && <Alert tone="success">{notice}</Alert>}
          {actionError && <Alert>{actionError}</Alert>}
          {listError ? (
            <div className="space-y-3">
              <Alert>{listError}</Alert>
              <button type="button" className={secondary} onClick={() => setRefresh((count) => count + 1)}>Tải lại danh sách</button>
            </div>
          ) : loading ? <div className={`${panel} p-4`}><Spinner label="Đang tải sản phẩm…" /></div> : (
            <SellerProductTable
              items={items}
              page={filter.page}
              hasMore={Boolean(result?.has_more)}
              filtered={filtered}
              changing={changing}
              onPage={(page) => setFilter((current) => ({ ...current, page }))}
              onEdit={(product) => openEditor({ mode: 'edit', product })}
              onVisibility={(products, status) => void changeVisibility(products, status)}
            />
          )}
        </div>
      )}
    </AppShell>
  )
}
