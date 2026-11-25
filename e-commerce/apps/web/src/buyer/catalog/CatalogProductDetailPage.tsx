import { useCallback, useState } from 'react'
import { Link, useLocation, useParams } from 'react-router-dom'
import { ApiError, api, type CatalogProductDetail } from '../../shared/api/client'
import { Alert, Spinner } from '../../shared/auth/components/ui'
import { BuyerStoreLayout } from '../BuyerStoreLayout'
import { AddToCart } from '../commerce/AddToCart'
import { Availability, CatalogError, ProductPhoto, catalogLink, productPrice } from './catalogUi'
import { catalogErrorMessage, useCatalogRequest } from './useCatalogRequest'

export default function CatalogProductDetailPage() {
  const { productId = '' } = useParams()
  const { state } = useLocation()
  const search = typeof state?.catalogSearch === 'string' ? state.catalogSearch : ''
  const back = search ? `/products?${search}` : '/products'

  return (
    <BuyerStoreLayout>
      <div className="mx-auto max-w-7xl space-y-5 px-4 py-7 sm:px-6 sm:py-10">
        <Link to={back} className={`inline-block ${catalogLink}`}><span aria-hidden>← </span>Quay lại danh sách sản phẩm</Link>
        <ProductDetail key={productId} id={productId} />
      </div>
    </BuyerStoreLayout>
  )
}

function ProductDetail({ id }: { id: string }) {
  const load = useCallback(() => api.catalogProduct(id), [id])
  const { state, retry } = useCatalogRequest(load)

  if (state.status === 'loading') return <Spinner label="Đang tải chi tiết sản phẩm…" />
  if (state.status === 'error') {
    if (state.error instanceof ApiError && [404, 422].includes(state.error.status)) {
      return <Alert>Sản phẩm không còn được đăng bán hoặc không tồn tại.</Alert>
    }
    return <CatalogError message={catalogErrorMessage(state.error, 'Không tải được chi tiết sản phẩm.')} retry={retry} />
  }
  const product = state.data
  const categories = product.parent_category ? [product.parent_category, product.category] : [product.category]

  return (
    <article className="grid gap-6 rounded-2xl border border-zinc-200 bg-white p-4 sm:p-6 md:grid-cols-2 md:gap-8 dark:border-zinc-800 dark:bg-zinc-900">
      <Gallery images={product.images} name={product.name} />
      <div className="min-w-0 space-y-5">
        <nav aria-label="Danh mục sản phẩm">
          <ol className="flex flex-wrap gap-2 text-sm">
            {categories.map(({ name, slug }, index) => (
              <li key={slug} className="flex items-center gap-2">
                {index > 0 && <span aria-hidden className="text-zinc-400">/</span>}
                <Link className="rounded text-brand-700 hover:underline dark:text-brand-100" to={`/products?${new URLSearchParams({ category: slug })}`}>{name}</Link>
              </li>
            ))}
          </ol>
        </nav>
        <div className="space-y-3">
          <h1 className="break-words text-3xl font-bold leading-tight tracking-tight">{product.name}</h1>
          {product.brand && <p className="break-words text-sm text-zinc-500 dark:text-zinc-400">Thương hiệu · {product.brand}</p>}
          <p className="break-words text-2xl font-bold text-brand-700 dark:text-brand-100">{productPrice.format(product.price)}</p>
          <Availability inStock={product.in_stock} />
        </div>
        <AddToCart productId={product.id} inStock={product.in_stock} />
        <dl className="rounded-xl bg-zinc-50 p-4 dark:bg-zinc-950">
          <dt className="text-sm text-zinc-500 dark:text-zinc-400">Gian hàng</dt>
          <dd className="break-words font-semibold">{product.shop.name}</dd>
          <dd className="mt-1 text-sm text-zinc-600 dark:text-zinc-300">{product.shop.province.name}</dd>
        </dl>
        {product.description?.trim() && (
          <section aria-labelledby="product-description" className="border-t border-zinc-200 pt-5 dark:border-zinc-800">
            <h2 id="product-description" className="mb-2 text-lg font-semibold">Mô tả sản phẩm</h2>
            <p className="whitespace-pre-wrap break-words text-sm leading-6 text-zinc-700 dark:text-zinc-300">{product.description}</p>
          </section>
        )}
      </div>
    </article>
  )
}

function Gallery({ images, name }: Pick<CatalogProductDetail, 'images' | 'name'>) {
  const [selected, setSelected] = useState(0)

  return (
    <div className="min-w-0 space-y-3">
      <div className="aspect-square overflow-hidden rounded-xl bg-zinc-100 p-4 dark:bg-zinc-800">
        <ProductPhoto key={selected} url={images[selected] ?? null} alt={`${name} — ảnh ${selected + 1}`} />
      </div>
      {images.length > 1 && (
        <div role="group" aria-label="Chọn ảnh sản phẩm" className="flex flex-wrap gap-2">
          {images.map((url, index) => (
            <button
              key={index}
              type="button"
              aria-label={`Xem ảnh ${index + 1}`}
              aria-pressed={selected === index}
              onClick={() => setSelected(index)}
              className="size-14 overflow-hidden rounded-lg border-2 border-zinc-200 bg-zinc-100 p-1 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-500 aria-pressed:border-brand-500 dark:border-zinc-700 dark:bg-zinc-800 dark:aria-pressed:border-brand-500 sm:size-16"
            >
              <ProductPhoto url={url} alt="" lazy />
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
