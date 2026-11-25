import { useCallback } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api, type CatalogProductCard } from '../../shared/api/client'
import { Spinner } from '../../shared/auth/components/ui'
import { BuyerStoreLayout } from '../BuyerStoreLayout'
import { CatalogFilters } from './CatalogFilters'
import { Availability, CatalogError, ProductPhoto, catalogLink, productPrice } from './catalogUi'
import { catalogErrorMessage, useCatalogRequest } from './useCatalogRequest'

export default function CatalogProductsPage() {
  const [params, setParams] = useSearchParams()
  const query = params.get('q')?.trim()
  const search = params.toString()

  return (
    <BuyerStoreLayout>
      <div className="mx-auto max-w-7xl px-4 py-7 sm:px-6 sm:py-10">
        <h1 className="mb-6 break-words text-3xl font-bold tracking-tight">
          {query ? `Kết quả tìm kiếm cho “${query}”` : 'Sản phẩm'}
        </h1>
        <div className="grid gap-6 lg:grid-cols-[16rem_minmax(0,1fr)]">
          <CatalogFilters params={params} apply={setParams} />
          <ProductResults key={search} search={search} />
        </div>
      </div>
    </BuyerStoreLayout>
  )
}

function ProductResults({ search }: { search: string }) {
  const load = useCallback(() => api.catalogProducts(new URLSearchParams(search)), [search])
  const { state, retry } = useCatalogRequest(load)
  const params = new URLSearchParams(search)
  const page = Number(params.get('page') ?? 1)
  const pageHref = (target: number) => {
    const next = new URLSearchParams(params)
    if (target === 1) next.delete('page')
    else next.set('page', String(target))
    return next.size ? `/products?${next}` : '/products'
  }

  if (state.status === 'loading') {
    return <div className="p-4"><Spinner label="Đang tải sản phẩm…" /></div>
  }
  if (state.status === 'error') {
    return (
      <div>
        <CatalogError message={catalogErrorMessage(state.error, 'Không tải được sản phẩm.')} retry={retry} />
        {search && <Link to="/products" className={`mt-2 inline-block ${catalogLink}`}>Xem tất cả sản phẩm</Link>}
      </div>
    )
  }

  const { items, has_more } = state.data
  return (
    <div className="min-w-0 space-y-6">
      {items.length ? (
        <ul aria-label="Danh sách sản phẩm" className="grid grid-cols-2 gap-3 sm:gap-4 md:grid-cols-3 xl:grid-cols-4">
          {items.map((product) => <ProductCard key={product.id} product={product} search={search} />)}
        </ul>
      ) : (
        <div className="rounded-2xl border border-dashed border-zinc-300 px-6 py-12 text-center dark:border-zinc-700">
          <h2 className="text-lg font-semibold">Không tìm thấy sản phẩm</h2>
          <p className="mt-2 text-sm text-zinc-500">
            {search ? 'Thử đổi từ khóa hoặc bớt bộ lọc.' : 'Các sản phẩm đang đăng bán sẽ hiển thị tại đây.'}
          </p>
        </div>
      )}
      {(page > 1 || has_more) && (
        <nav aria-label="Phân trang sản phẩm" className="flex flex-wrap items-center justify-center gap-3 text-sm">
          {page > 1 && <Link to={pageHref(page - 1)} className={catalogLink} rel="prev">Trang trước</Link>}
          <span className="rounded-lg bg-zinc-200 px-3 py-2 font-medium dark:bg-zinc-800" aria-current="page">Trang {page}</span>
          {has_more && page < 100_000 && <Link to={pageHref(page + 1)} className={catalogLink} rel="next">Trang sau</Link>}
        </nav>
      )}
    </div>
  )
}

function ProductCard({ product, search }: { product: CatalogProductCard; search: string }) {
  return (
    <li className="min-w-0">
      <Link
        to={`/products/${product.id}`}
        state={{ catalogSearch: search }}
        className="flex h-full flex-col overflow-hidden rounded-2xl border border-zinc-200 bg-white transition hover:border-brand-500 hover:shadow-md focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-500 dark:border-zinc-800 dark:bg-zinc-900"
      >
        <div className="aspect-square bg-zinc-100 p-3 dark:bg-zinc-800">
          <ProductPhoto url={product.image_url} alt="" lazy />
        </div>
        <div className="flex flex-1 flex-col gap-2 p-3 sm:p-4">
          {product.brand && <p className="break-words text-xs text-zinc-500 dark:text-zinc-400">{product.brand}</p>}
          <h2 className="break-words text-sm font-semibold leading-5 sm:text-base">{product.name}</h2>
          <p className="break-words font-bold text-brand-700 dark:text-brand-100">{productPrice.format(product.price)}</p>
          <div className="mt-auto space-y-1">
            <p className="break-words text-xs text-zinc-500 dark:text-zinc-400">{product.shop.name} · {product.shop.province.name}</p>
            <Availability inStock={product.in_stock} />
          </div>
        </div>
      </Link>
    </li>
  )
}
