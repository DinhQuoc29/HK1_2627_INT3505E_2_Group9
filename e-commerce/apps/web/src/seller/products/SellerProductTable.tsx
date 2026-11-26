import { useEffect, useRef, useState } from 'react'
import type { ProductStatus, SellerProduct } from '../../shared/api/client'
import { SellerIcon } from '../sellerUi'
import { imageUrl } from './ProductForm'

const number = new Intl.NumberFormat('vi-VN')
const money = new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' })
const focus = 'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-(--seller-accent)'
const outlineButton = `inline-flex min-h-9 items-center justify-center rounded-md border border-slate-200 bg-white px-2.5 text-xs font-medium whitespace-nowrap text-slate-700 transition-colors hover:border-slate-300 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50 ${focus}`
const cell = 'min-w-0 @min-[48rem]:table-cell @min-[48rem]:px-3 @min-[48rem]:py-3 @min-[48rem]:align-middle'
const mobileLabel = 'mb-0.5 block text-[11px] font-medium text-slate-500 @min-[48rem]:hidden'

export function isLowStock(quantity: number) {
  return quantity > 0 && quantity <= 5
}

function SelectProduct({ label, checked, mixed = false, disabled, onChange }: {
  label: string
  checked: boolean
  mixed?: boolean
  disabled: boolean
  onChange: () => void
}) {
  const input = useRef<HTMLInputElement>(null)
  useEffect(() => {
    if (input.current) input.current.indeterminate = mixed
  }, [mixed])

  return (
    <input
      ref={input}
      type="checkbox"
      aria-label={label}
      checked={checked}
      disabled={disabled}
      onChange={onChange}
      className={`size-4 shrink-0 cursor-pointer align-middle accent-(--seller-accent) disabled:cursor-not-allowed ${focus}`}
    />
  )
}

function ProductRow({ product, selected, changing, onSelect, onEdit, onVisibility }: {
  product: SellerProduct
  selected: boolean
  changing: boolean
  onSelect: () => void
  onEdit: () => void
  onVisibility: (status: ProductStatus) => void
}) {
  const cover = imageUrl(product.images[0] ?? '')
  const active = product.status === 'active'
  const lowStock = isLowStock(product.quantity)
  const outOfStock = product.quantity === 0

  return (
    <tr role="row" className="grid grid-cols-2 gap-x-4 gap-y-3 p-3.5 text-[13px] text-slate-700 transition-colors hover:bg-slate-50/70 @min-[48rem]:table-row">
      <td role="cell" className={`${cell} col-start-1 row-start-1 z-10 w-fit self-start pt-3 @min-[48rem]:w-auto @min-[48rem]:text-center`}>
        <SelectProduct label={`Chọn ${product.name}`} checked={selected} disabled={changing} onChange={onSelect} />
      </td>
      <th scope="row" role="rowheader" className={`${cell} col-span-2 col-start-1 row-start-1 pl-8 text-left font-medium`}>
        <div className="flex min-w-0 items-center gap-3">
          <div className="relative grid size-11 shrink-0 place-items-center overflow-hidden rounded-md border border-slate-200 bg-slate-50 text-slate-400">
            <SellerIcon name="products" />
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
            <span className="block font-semibold text-slate-900 wrap-anywhere">{product.name}</span>
            {product.brand && <span className="mt-0.5 block text-[11px] text-slate-500 wrap-anywhere">{product.brand}</span>}
          </div>
        </div>
      </th>
      <td role="cell" className={`${cell} col-span-2 row-start-2`}>
        <span className="inline-block rounded bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600 wrap-anywhere">{product.category_name}</span>
      </td>
      <td role="cell" className={`${cell} row-start-3`}>
        <span className={mobileLabel}>Giá bán</span>
        <span className="font-medium text-slate-900 tabular-nums wrap-anywhere">{money.format(product.price)}</span>
      </td>
      <td role="cell" className={`${cell} row-start-3`}>
        <span className={mobileLabel}>Tồn kho</span>
        <span className={`inline-flex items-center gap-1.5 tabular-nums ${outOfStock ? 'font-medium text-red-700' : lowStock ? 'font-medium text-amber-700' : ''}`}>
          <span aria-hidden="true" className={`size-1.5 shrink-0 rounded-full ${outOfStock ? 'bg-red-500' : lowStock ? 'bg-amber-500' : 'bg-emerald-500'}`} />
          {outOfStock ? 'Hết hàng' : `Tồn ${number.format(product.quantity)}`}
        </span>
      </td>
      <td role="cell" className={`${cell} row-start-4 self-center`}>
        <span className={`inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-xs font-medium ${active
          ? 'border-emerald-200/60 bg-emerald-50 text-emerald-700'
          : 'border-slate-200 bg-slate-100 text-slate-600'}`}>
          <span aria-hidden="true" className={`size-1.5 shrink-0 rounded-full ${active ? 'bg-emerald-500' : 'bg-slate-400'}`} />
          {active ? 'Đang hiển thị' : 'Đã ẩn'}
        </span>
      </td>
      <td role="cell" className={`${cell} row-start-4`}>
        <div className="flex flex-wrap justify-end gap-1">
          <button type="button" className={outlineButton} disabled={changing} onClick={onEdit} aria-label={`Sửa ${product.name}`}>Sửa</button>
          <button
            type="button"
            className={outlineButton}
            disabled={changing}
            onClick={() => onVisibility(active ? 'inactive' : 'active')}
            aria-label={`${active ? 'Ẩn' : 'Hiển thị'} ${product.name}`}
          >
            {active ? 'Ẩn' : 'Hiển thị'}
          </button>
        </div>
      </td>
    </tr>
  )
}

const columns = ['Sản phẩm', 'Danh mục', 'Giá bán', 'Tồn kho', 'Trạng thái', 'Thao tác']

export function SellerProductTable({ items, page, hasMore, filtered, changing, onPage, onEdit, onVisibility }: {
  items: SellerProduct[]
  page: number
  hasMore: boolean
  filtered: boolean
  changing: boolean
  onPage: (page: number) => void
  onEdit: (product: SellerProduct) => void
  onVisibility: (products: SellerProduct[], status: ProductStatus) => void
}) {
  const [selectedIds, setSelectedIds] = useState<Set<string>>(() => new Set())
  const selected = items.filter(({ id }) => selectedIds.has(id))
  const allSelected = items.length > 0 && selected.length === items.length

  const toggleAll = () => setSelectedIds(allSelected ? new Set() : new Set(items.map(({ id }) => id)))
  const toggleRow = (id: string) => setSelectedIds((current) => {
    const next = new Set(current)
    if (next.has(id)) next.delete(id)
    else next.add(id)
    return next
  })

  const selectAll = (
    <SelectProduct label="Chọn tất cả sản phẩm trên trang" checked={allSelected} mixed={selected.length > 0 && !allSelected} disabled={changing} onChange={toggleAll} />
  )

  return (
    <section aria-label="Danh sách sản phẩm" className="@container overflow-hidden rounded-lg border border-slate-200 bg-white shadow-xs">
      {items.length > 0 ? (
        <>
          <div className={`flex flex-wrap items-center gap-2 border-b border-slate-200 bg-slate-50/80 px-3.5 py-2 text-xs text-slate-600 ${selected.length ? '' : '@min-[48rem]:hidden'}`}>
            <label className="mr-1 inline-flex min-h-9 items-center gap-2 @min-[48rem]:hidden">
              {selectAll}
              Chọn tất cả
            </label>
            {selected.length > 0 && (
              <>
                <span className="font-semibold text-slate-800">Đã chọn {number.format(selected.length)}</span>
                <button type="button" className={outlineButton} disabled={changing || !selected.some(({ status }) => status === 'active')} onClick={() => onVisibility(selected, 'inactive')}>Ẩn đã chọn</button>
                <button type="button" className={outlineButton} disabled={changing || !selected.some(({ status }) => status === 'inactive')} onClick={() => onVisibility(selected, 'active')}>Hiện đã chọn</button>
              </>
            )}
          </div>
          <table aria-label="Sản phẩm trong gian hàng" role="table" className="block w-full text-left @min-[48rem]:table @min-[48rem]:table-fixed">
            <colgroup className="hidden @min-[48rem]:table-column-group">
              <col className="w-11" />
              <col />
              <col className="w-[17%]" />
              <col className="w-[14%]" />
              <col className="w-[12%]" />
              <col className="w-[16%]" />
              <col className="w-32" />
            </colgroup>
            <thead role="rowgroup" className="hidden @min-[48rem]:table-header-group">
              <tr role="row" className="border-b border-slate-200 bg-slate-50/80 text-xs font-semibold tracking-wide whitespace-nowrap text-slate-500 uppercase">
                <th scope="col" role="columnheader" className="px-3 py-3.5 text-center">{selectAll}</th>
                {columns.map((column) => <th key={column} scope="col" role="columnheader" className="px-3 py-3.5 last:text-right">{column}</th>)}
              </tr>
            </thead>
            <tbody role="rowgroup" className="block divide-y divide-slate-100 @min-[48rem]:table-row-group">
              {items.map((product) => (
                <ProductRow
                  key={product.id}
                  product={product}
                  selected={selectedIds.has(product.id)}
                  changing={changing}
                  onSelect={() => toggleRow(product.id)}
                  onEdit={() => onEdit(product)}
                  onVisibility={(status) => onVisibility([product], status)}
                />
              ))}
            </tbody>
          </table>
        </>
      ) : (
        <div className="px-4 py-10 text-center">
          <p className="text-sm font-semibold">{filtered ? 'Không tìm thấy sản phẩm phù hợp.' : 'Chưa có sản phẩm.'}</p>
          <p className="mt-1 text-[13px] text-slate-500">{filtered ? 'Thử đổi từ khóa hoặc trạng thái.' : 'Dùng nút Thêm sản phẩm để tạo sản phẩm đầu tiên.'}</p>
        </div>
      )}
      <div className="flex flex-wrap items-center justify-between gap-2 border-t border-slate-200 bg-slate-50/80 px-4 py-2.5">
        <p className="text-xs text-slate-500">
          Hiển thị <strong className="font-semibold text-slate-700">{number.format(items.length)}</strong>
          {page === 1 && !hasMore && <> trên <strong className="font-semibold text-slate-700">{number.format(items.length)}</strong></>}
          {' sản phẩm'}
        </p>
        <nav aria-label="Phân trang sản phẩm" className="flex items-center gap-1">
          <button type="button" aria-label="Trang trước" className={outlineButton} disabled={changing || page === 1} onClick={() => onPage(page - 1)}>
            <SellerIcon name="chevron" className="size-4 rotate-180" />
          </button>
          <span aria-current="page" aria-label={`Trang ${page}`} className="grid min-h-9 min-w-9 place-items-center rounded-md bg-(--seller-accent) px-1.5 text-xs font-semibold text-white">{number.format(page)}</span>
          <button type="button" aria-label="Trang sau" className={outlineButton} disabled={changing || !hasMore} onClick={() => onPage(page + 1)}>
            <SellerIcon name="chevron" className="size-4" />
          </button>
        </nav>
      </div>
    </section>
  )
}
