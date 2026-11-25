import { useEffect, useState } from 'react'
import { api, type ProductCategory, type ProductInput, type ProductStatus, type SellerProduct, type SellerProductPage } from '../../shared/api/client'
import { Alert, Button, Spinner } from '../../shared/auth/components/ui'
import { describeError } from '../../shared/auth/errors'
import { AppShell } from '../../shared/layout/AppShell'
import { imageUrl, ProductForm } from './ProductForm'

type Editor = { mode: 'create' } | { mode: 'edit'; product: SellerProduct }

const panel = 'rounded-2xl border border-zinc-200 bg-white p-4 shadow-sm sm:p-5 dark:border-zinc-800 dark:bg-zinc-900'
const control = 'min-h-11 min-w-0 rounded-xl border border-zinc-300 bg-white px-3 text-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-500 dark:border-zinc-700 dark:bg-zinc-900'
const secondary = 'min-h-11 rounded-xl border border-zinc-300 px-3 text-sm font-semibold hover:bg-zinc-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-500 disabled:cursor-not-allowed disabled:opacity-50 dark:border-zinc-700 dark:hover:bg-zinc-800'
const money = new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' })
const stockNumber = new Intl.NumberFormat('vi-VN')

function ProductRow({ product, disabled, onEdit, onToggle }: {
  product: SellerProduct
  disabled: boolean
  onEdit: () => void
  onToggle: () => void
}) {
  const cover = imageUrl(product.images[0] ?? '')
  const active = product.status === 'active'
  return (
    <li className="grid gap-4 p-4 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center">
      <div className="flex min-w-0 items-start gap-3">
        <div className="relative grid size-16 shrink-0 place-items-center overflow-hidden rounded-xl bg-zinc-100 text-center text-xs text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400">
          <span aria-hidden="true">Ảnh</span>
          {cover && (
            <img
              key={cover}
              src={cover}
              alt=""
              loading="lazy"
              decoding="async"
              referrerPolicy="no-referrer"
              className="absolute inset-0 size-full object-cover"
              onError={(event) => { event.currentTarget.hidden = true }}
            />
          )}
        </div>
        <div className="min-w-0">
          <h2 className="font-semibold wrap-anywhere">{product.name}</h2>
          <p className="mt-0.5 text-sm wrap-anywhere text-zinc-600 dark:text-zinc-400">
            {product.category_name}{product.brand ? ` · ${product.brand}` : ''}
          </p>
          <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm">
            <strong className="font-semibold tabular-nums">{money.format(product.price)}</strong>
            <span className="text-zinc-600 tabular-nums dark:text-zinc-400">{product.quantity ? `Tồn ${stockNumber.format(product.quantity)}` : 'Hết hàng'}</span>
            <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${active
              ? 'bg-emerald-50 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-200'
              : 'bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300'}`}>
              {active ? 'Đang hiển thị' : 'Đã ẩn'}
            </span>
          </div>
        </div>
      </div>
      <div className="flex flex-wrap gap-2">
        <button type="button" className={secondary} disabled={disabled} onClick={onEdit} aria-label={`Sửa ${product.name}`}>Sửa</button>
        <button type="button" className={secondary} disabled={disabled} onClick={onToggle} aria-label={`${active ? 'Ẩn' : 'Hiển thị'} ${product.name}`}>
          {active ? 'Ẩn' : 'Hiển thị'}
        </button>
      </div>
    </li>
  )
}

export default function SellerProductsPage() {
  const [filter, setFilter] = useState<{ q: string; status: ProductStatus | ''; page: number }>({ q: '', status: '', page: 1 })
  const [search, setSearch] = useState('')
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

  const toggle = async (product: SellerProduct) => {
    const nextStatus = product.status === 'active' ? 'inactive' : 'active'
    setChanging(true)
    setActionError(undefined)
    setNotice(undefined)
    try {
      await api.changeSellerProductStatus(product.id, nextStatus)
      setNotice(nextStatus === 'active' ? 'Đã hiển thị lại sản phẩm.' : 'Đã ẩn sản phẩm.')
      setRefresh((count) => count + 1)
    } catch (error) {
      setActionError(describeError(error).message ?? 'Không cập nhật được trạng thái sản phẩm.')
    } finally {
      setChanging(false)
    }
  }

  return (
    <AppShell>
      <div className="flex flex-wrap items-end justify-between gap-3 pb-4">
        <div className="min-w-0">
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">{editor ? (editor.mode === 'create' ? 'Thêm sản phẩm' : 'Sửa sản phẩm') : 'Sản phẩm'}</h1>
          <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">{editor ? 'Cập nhật thông tin, ảnh và số lượng tồn kho.' : 'Quản lý sản phẩm và tình trạng hiển thị trong gian hàng.'}</p>
        </div>
        {!editor && <div className="w-fit"><Button disabled={changing} onClick={() => openEditor({ mode: 'create' })}>Thêm sản phẩm</Button></div>}
      </div>

      {editor ? (
        <section aria-label="Thông tin sản phẩm" className={panel}>
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
        <>
          <form
            aria-label="Tìm và lọc sản phẩm"
            className={`grid gap-3 sm:grid-cols-[minmax(0,1fr)_auto_auto] ${panel}`}
            onSubmit={(event) => { event.preventDefault(); setFilter((current) => ({ ...current, q: search.trim(), page: 1 })) }}
          >
            <input type="search" className={control} aria-label="Tìm theo tên sản phẩm" placeholder="Tìm theo tên sản phẩm…" maxLength={255} value={search} onChange={(event) => setSearch(event.target.value)} />
            <select className={control} aria-label="Lọc theo trạng thái" value={filter.status} onChange={(event) => setFilter((current) => ({ ...current, status: event.target.value as ProductStatus | '', page: 1 }))}>
              <option value="">Mọi trạng thái</option>
              <option value="active">Đang hiển thị</option>
              <option value="inactive">Đã ẩn</option>
            </select>
            <button type="submit" className={secondary}>Tìm kiếm</button>
          </form>
          {notice && <Alert tone="success">{notice}</Alert>}
          {actionError && <Alert>{actionError}</Alert>}
          {listError ? (
            <div className="space-y-3">
              <Alert>{listError}</Alert>
              <button type="button" className={secondary} onClick={() => setRefresh((count) => count + 1)}>Tải lại danh sách</button>
            </div>
          ) : loading ? <div className={panel}><Spinner label="Đang tải sản phẩm…" /></div> : (
            <>
              {result?.items.length ? (
                <ul aria-label="Danh sách sản phẩm" className="divide-y divide-zinc-200 rounded-2xl border border-zinc-200 bg-white shadow-sm dark:divide-zinc-800 dark:border-zinc-800 dark:bg-zinc-900">
                  {result.items.map((product) => (
                    <ProductRow key={product.id} product={product} disabled={changing} onEdit={() => openEditor({ mode: 'edit', product })} onToggle={() => void toggle(product)} />
                  ))}
                </ul>
              ) : (
                <div className={`py-10 text-center ${panel}`}>
                  <p className="font-semibold">{filter.q || filter.status ? 'Không tìm thấy sản phẩm phù hợp.' : 'Chưa có sản phẩm.'}</p>
                  <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">{filter.q || filter.status ? 'Thử đổi từ khóa hoặc trạng thái.' : 'Dùng nút Thêm sản phẩm để tạo sản phẩm đầu tiên.'}</p>
                </div>
              )}
              {(filter.page > 1 || result?.has_more) && (
                <nav aria-label="Phân trang sản phẩm" className="flex flex-wrap items-center justify-end gap-2">
                  <button type="button" className={secondary} disabled={filter.page === 1} onClick={() => setFilter((current) => ({ ...current, page: current.page - 1 }))}>Trang trước</button>
                  <span className="px-1 text-sm tabular-nums">Trang {filter.page}</span>
                  <button type="button" className={secondary} disabled={!result?.has_more} onClick={() => setFilter((current) => ({ ...current, page: current.page + 1 }))}>Trang sau</button>
                </nav>
              )}
            </>
          )}
        </>
      )}
    </AppShell>
  )
}
