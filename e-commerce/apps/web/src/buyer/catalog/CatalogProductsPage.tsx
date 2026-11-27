import { useCallback } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api, type CatalogProductCard } from '../../shared/api/client'
import { BuyerStoreLayout } from '../../shared/layout/BuyerStoreLayout'
import { StoreIcon } from '../../shared/layout/StoreIcon'
import { BuyerLoading, BuyerRequestError } from '../BuyerFeedback'
import { buyerErrorMessage, useBuyerRequest } from '../useBuyerRequest'
import { CatalogFilters, catalogFilterKeys } from './CatalogFilters'
import { FavoriteProductButton, ProductPhoto, productPrice, useProductFavorites } from './catalogUi'

const resetClass = 'inline-flex min-h-9 items-center rounded-full bg-[#ffdad3] px-4 text-xs font-semibold text-[#3f0400] transition-colors hover:bg-(--store-primary) hover:text-white'
const pageControl = 'grid size-10 place-items-center rounded-lg text-sm font-semibold shadow-xs'
const pageLink = `${pageControl} bg-white text-(--store-muted) transition hover:text-(--store-primary) hover:shadow-md`

function catalogHref(params: URLSearchParams) {
  return params.size ? `/products?${params}` : '/products'
}

export default function CatalogProductsPage() {
  const [params, setParams] = useSearchParams()
  const query = params.get('q')?.trim()
  const search = params.toString()
  const load = useCallback(() => api.catalogProducts(new URLSearchParams(search)), [search])
  const { state, retry } = useBuyerRequest(load)
  const { favorites, toggleFavorite } = useProductFavorites()

  const filtered = catalogFilterKeys.some((key) => params.has(key))
  const cleared = new URLSearchParams(params)
  for (const key of catalogFilterKeys) cleared.delete(key)
  cleared.delete('page')
  const reset = catalogHref(cleared)

  function applyFilters(update: (next: URLSearchParams) => void) {
    const next = new URLSearchParams(params)
    update(next)
    next.delete('page')
    setParams(next)
  }

  return (
    <BuyerStoreLayout storefront>
      <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:py-10 lg:px-8">
        <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
          <div className="min-w-0">
            <p className="mb-1 text-xs font-semibold tracking-[.12em] text-(--store-primary) uppercase">E-Market Catalog</p>
            <h1 id="catalog-title" className="scroll-mt-32 text-2xl leading-8 font-bold tracking-tight wrap-anywhere md:scroll-mt-24 md:text-[32px] md:leading-10">
              {query ? `Kết quả tìm kiếm cho “${query}”` : 'Tất cả sản phẩm'}
            </h1>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <div role="status" className="text-sm text-(--store-muted)">
              {state.status === 'ready' && (
                <span className="inline-flex items-center gap-2 rounded-full bg-(--store-soft) px-4 py-2">
                  <span aria-hidden="true" className="size-2 rounded-full bg-[#006947]" />
                  Hiển thị {state.data.items.length} sản phẩm
                </span>
              )}
            </div>
            {filtered && <Link to={reset} className={resetClass}>Xóa bộ lọc</Link>}
          </div>
        </div>

        <div className="grid items-start gap-5 lg:grid-cols-[15rem_minmax(0,1fr)] lg:gap-10">
          <CatalogFilters params={params} apply={applyFilters} />
          <div className="min-w-0">
            {state.status === 'loading' && <BuyerLoading label="Đang tải sản phẩm…" />}
            {state.status === 'error' && (
              <div className="rounded-xl bg-white p-4 shadow-xs">
                <BuyerRequestError message={buyerErrorMessage(state.error, 'Không tải được sản phẩm.')} retry={retry} />
                {search && <Link to="/products" className={resetClass}>Xem tất cả sản phẩm</Link>}
              </div>
            )}
            {state.status === 'ready' && (
              <>
                {state.data.items.length > 0 ? (
                  <ul aria-label="Danh sách sản phẩm" className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-4 lg:gap-6">
                    {state.data.items.map((product) => (
                      <ProductCard key={product.id} product={product} search={search} favorite={favorites.includes(product.id)} toggleFavorite={() => toggleFavorite(product.id)} />
                    ))}
                  </ul>
                ) : (
                  <div className="flex flex-col items-center gap-4 rounded-xl bg-white p-8 text-center shadow-xs sm:p-10">
                    <div className="grid size-14 place-items-center rounded-full bg-(--store-soft) text-(--store-muted)"><StoreIcon name="search" /></div>
                    <div className="space-y-1">
                      <h2 className="text-xl font-semibold">Không tìm thấy sản phẩm phù hợp</h2>
                      <p className="text-sm text-(--store-muted)">
                        {query || filtered ? 'Thử đổi từ khóa hoặc điều chỉnh bộ lọc.' : 'Các sản phẩm đang đăng bán sẽ hiển thị tại đây.'}
                      </p>
                    </div>
                    {filtered && <Link to={reset} className={resetClass}>Đặt lại bộ lọc</Link>}
                    {!filtered && query && <Link to="/products" className={resetClass}>Xem tất cả sản phẩm</Link>}
                  </div>
                )}
                <CatalogPagination params={params} hasMore={state.data.has_more} />
              </>
            )}
          </div>
        </div>
      </div>
    </BuyerStoreLayout>
  )
}

function CatalogPagination({ params, hasMore }: { params: URLSearchParams; hasMore: boolean }) {
  const page = Number(params.get('page') ?? 1)
  const hasNext = hasMore && page < 100_000
  if (page === 1 && !hasNext) return null

  function pageHref(target: number) {
    const next = new URLSearchParams(params)
    if (target === 1) next.delete('page')
    else next.set('page', String(target))
    return `${catalogHref(next)}#catalog-title`
  }

  return (
    <nav aria-label="Phân trang sản phẩm" className="mt-8 flex flex-wrap items-center justify-center gap-2 sm:mt-14">
      {page > 1 ? (
        <Link to={pageHref(page - 1)} rel="prev" aria-label="Trang trước" className={pageLink}><StoreIcon name="chevron" className="size-5 rotate-180" /></Link>
      ) : <span aria-hidden="true" className={`${pageControl} bg-white/70 text-(--store-muted)/45`}><StoreIcon name="chevron" className="size-5 rotate-180" /></span>}
      {page > 1 && <Link to={pageHref(page - 1)} aria-label={`Trang ${page - 1}`} className={pageLink}>{page - 1}</Link>}
      <span aria-current="page" aria-label={`Trang ${page}`} className={`${pageControl} min-w-10 w-auto bg-(--store-primary) px-2 text-white`}>{page}</span>
      {hasNext && <Link to={pageHref(page + 1)} aria-label={`Trang ${page + 1}`} className={pageLink}>{page + 1}</Link>}
      {hasNext ? (
        <Link to={pageHref(page + 1)} rel="next" aria-label="Trang sau" className={pageLink}><StoreIcon name="chevron" className="size-5" /></Link>
      ) : <span aria-hidden="true" className={`${pageControl} bg-white/70 text-(--store-muted)/45`}><StoreIcon name="chevron" className="size-5" /></span>}
    </nav>
  )
}

function ProductCard({ product, search, favorite, toggleFavorite }: { product: CatalogProductCard; search: string; favorite: boolean; toggleFavorite: () => void }) {
  return (
    <li className="group relative min-w-0 rounded-xl bg-white p-3 shadow-xs transition-shadow hover:shadow-md sm:p-4">
      <Link to={`/products/${product.id}`} state={{ catalogSearch: search }} className="flex h-full min-w-0 flex-col gap-2 rounded-lg">
        <div className="relative aspect-square overflow-hidden rounded-lg bg-(--store-soft)">
          <ProductPhoto url={product.image_url} alt="" lazy cover />
          {!product.in_stock && <span className="absolute bottom-2 left-2 rounded-md bg-white/95 px-2 py-1 text-xs text-(--store-muted)">Hết hàng</span>}
        </div>
        <div className="flex flex-1 flex-col gap-1 pt-1">
          <p className="truncate text-xs text-(--store-muted)" title={[product.shop.name, product.shop.province.name, product.brand].filter(Boolean).join(' · ')}>{product.shop.name}</p>
          <h2 className="line-clamp-2 min-h-10 text-sm leading-5 font-semibold wrap-anywhere transition-colors group-hover:text-(--store-primary) sm:min-h-12 sm:text-base sm:leading-6">{product.name}</h2>
          <p className="mt-auto pt-1 text-base font-semibold wrap-anywhere text-(--store-primary) tabular-nums sm:text-xl">{productPrice.format(product.price)}</p>
        </div>
      </Link>
      <FavoriteProductButton name={product.name} pressed={favorite} toggle={toggleFavorite} />
    </li>
  )
}
