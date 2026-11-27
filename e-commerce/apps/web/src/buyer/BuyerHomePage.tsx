import { useCallback, useState, type ComponentProps, type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { api, type CatalogProductCard, type CatalogProductPage } from '../shared/api/client'
import { BuyerStoreLayout } from '../shared/layout/BuyerStoreLayout'
import { StoreIcon } from '../shared/layout/StoreIcon'
import { BuyerEmptyState, BuyerLoading, BuyerRequestError } from './BuyerFeedback'
import { FavoriteProductButton, ProductPhoto, productPrice, useProductFavorites } from './catalog/catalogUi'
import { useBuyerRequest } from './useBuyerRequest'

const categoryIcons = new Map<string, ComponentProps<typeof StoreIcon>['name']>([
  ['giay-dep', 'shoe'],
  ['trang-tri-nha-cua', 'chair'],
  ['tui-va-phu-kien', 'watch'],
  ['thoi-trang', 'shirt'],
  ['dien-tu', 'headphones'],
  ['cham-soc-ca-nhan', 'leaf'],
  ['sach-va-van-phong-pham', 'book'],
  ['nha-cua-va-doi-song', 'chair'],
])

const budgetRanges = [
  { label: 'Tất cả' },
  { label: 'Dưới 200.000 ₫', max: '199999' },
  { label: '200.000 ₫ – 500.000 ₫', min: '200000', max: '500000' },
  { label: 'Trên 500.000 ₫', min: '500001' },
]

const cardsPerSection = 4
const loadHomeProducts = () => api.catalogProducts(new URLSearchParams({ limit: String(cardsPerSection * 2) }))
const sectionLinkClass = 'inline-flex shrink-0 items-center gap-1 rounded-sm py-1 text-sm font-semibold text-(--store-primary) hover:text-(--store-primary-hover)'
const productGridClass = 'grid grid-cols-2 gap-3 sm:gap-6 md:grid-cols-3 lg:grid-cols-4'

export default function BuyerHomePage() {
  return (
    <BuyerStoreLayout storefront>
      <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:py-10 lg:px-8">
        <section className="grid overflow-hidden rounded-xl bg-white shadow-xs lg:min-h-[520px] lg:grid-cols-[5fr_7fr]" aria-labelledby="store-hero-title">
          <div className="flex flex-col items-start justify-center gap-6 px-6 py-9 sm:p-10 lg:p-12">
            <p className="flex items-center gap-2 text-xs font-semibold tracking-[.12em] text-(--store-primary) uppercase">
              <span className="h-0.5 w-6 bg-current" aria-hidden="true" /> E-Market Curated
            </p>
            <h1 id="store-hero-title" className="max-w-xl text-[32px] leading-[1.16] font-extrabold tracking-tight lg:text-5xl lg:leading-[1.17]">
              Mua sắm thông minh, đúng thứ bạn cần.
            </h1>
            <p className="max-w-md text-base leading-6 text-(--store-muted)">
              Khám phá sản phẩm phù hợp với phong cách và ngân sách của bạn.
            </p>
            <div className="flex flex-wrap gap-2 pt-2 text-sm font-semibold sm:gap-4">
              <a href="#san-pham-noi-bat" className="inline-flex min-h-12 items-center gap-2 rounded-lg bg-(--store-primary) px-3.5 text-white shadow-sm transition-colors hover:bg-(--store-primary-hover) sm:px-6">
                Khám phá ngay <StoreIcon name="arrow" className="size-[18px]" />
              </a>
              <a href="#danh-muc" className="inline-flex min-h-12 items-center rounded-lg bg-(--store-soft) px-3.5 transition-colors hover:bg-(--store-soft-hover) sm:px-5">
                Xem danh mục
              </a>
            </div>
          </div>
          <div className="relative h-[clamp(13rem,50vw,20rem)] overflow-hidden lg:h-full lg:min-h-[520px]">
            <img
              src="/login-marketplace.png"
              alt="Bộ sưu tập giày sneaker, tai nghe, túi xách và phụ kiện E-Market"
              width={1200}
              height={896}
              fetchPriority="high"
              className="absolute inset-0 size-full object-cover"
            />
            <div aria-hidden="true" className="pointer-events-none absolute inset-x-0 top-0 h-8 bg-linear-to-b from-white to-transparent lg:inset-y-0 lg:right-auto lg:h-auto lg:w-24 lg:bg-linear-to-r" />
          </div>
        </section>

        <section id="danh-muc" aria-labelledby="buyer-categories" className="mt-10 scroll-mt-32 md:scroll-mt-24 lg:mt-14">
          <SectionHeading id="buyer-categories" label="Danh mục" title="Khám phá danh mục">
            <Link to="/products#catalog-filters" className={sectionLinkClass}>
              Tất cả danh mục <StoreIcon name="chevron" className="size-[18px]" />
            </Link>
          </SectionHeading>
          <HomeCategories />
        </section>

        <HomeProducts />
      </div>
    </BuyerStoreLayout>
  )
}

function SectionHeading({ id, label, title, children }: { id: string; label: string; title: string; children: ReactNode }) {
  return (
    <div className="mb-4 flex flex-wrap items-end justify-between gap-x-4 gap-y-3 sm:mb-6">
      <div>
        <p className="mb-1 text-xs font-semibold tracking-[.12em] text-(--store-muted) uppercase">{label}</p>
        <h2 id={id} className="text-xl leading-8 font-semibold tracking-tight sm:text-2xl">{title}</h2>
      </div>
      {children}
    </div>
  )
}

function HomeCategories() {
  const { state, retry } = useBuyerRequest(api.catalogCategories)
  if (state.status === 'loading') return <BuyerLoading label="Đang tải danh mục…" />
  if (state.status === 'error') return <BuyerRequestError message="Không tải được danh mục." retry={retry} />
  if (!state.data.length) return <BuyerEmptyState title="Chưa có danh mục sản phẩm" />

  const allCategories = state.data.flatMap((category) => [category, ...category.children])
  const categories = new Map(allCategories.map((category) => [category.slug, category]))
  const selected = [...new Set([...categoryIcons.keys(), ...categories.keys()])].flatMap((slug) => {
    const category = categories.get(slug)
    return category ? [category] : []
  }).slice(0, 6)

  return (
    <ul className="grid grid-cols-2 gap-3 sm:grid-cols-3 sm:gap-4 lg:grid-cols-6">
      {selected.map(({ slug, name }) => (
        <li key={slug} className="min-w-0">
          <Link to={`/products?${new URLSearchParams({ category: slug })}`} className="group flex h-full min-h-32 flex-col items-center justify-center gap-2 rounded-xl bg-white p-4 text-center text-sm font-semibold shadow-xs transition hover:-translate-y-0.5 hover:shadow-md sm:min-h-44 sm:p-6 sm:text-base">
            <span className="grid size-12 place-items-center rounded-full bg-(--store-soft) transition-colors group-hover:bg-(--store-primary) group-hover:text-white">
              <StoreIcon name={categoryIcons.get(slug) ?? 'grid'} />
            </span>
            <span className="wrap-anywhere">{name}</span>
          </Link>
        </li>
      ))}
    </ul>
  )
}

function HomeProducts() {
  const request = useBuyerRequest(loadHomeProducts)
  const [range, setRange] = useState(budgetRanges[0])
  const { favorites, toggleFavorite } = useProductFavorites()

  return (
    <>
      <section id="san-pham-noi-bat" aria-labelledby="buyer-featured" className="mt-12 scroll-mt-32 md:scroll-mt-24 lg:mt-16">
        <SectionHeading id="buyer-featured" label="Tuyển chọn" title="Sản phẩm nổi bật">
          <Link to="/products" className={sectionLinkClass}>Xem tất cả <StoreIcon name="chevron" className="size-[18px]" /></Link>
        </SectionHeading>
        <HomeProductResults request={request} emptyTitle="Chưa có sản phẩm nổi bật">
          {(items) => (
            <ul className={productGridClass}>
              {items.slice(0, cardsPerSection).map((product) => (
                <HomeProductCard key={product.id} product={product} favorite={favorites.includes(product.id)} onFavorite={() => toggleFavorite(product.id)} />
              ))}
            </ul>
          )}
        </HomeProductResults>
      </section>

      <section aria-labelledby="buyer-budget" className="mt-12 lg:mt-16">
        <SectionHeading id="buyer-budget" label="Gợi ý cho bạn" title="Sản phẩm phù hợp ngân sách">
          <div role="group" aria-label="Khoảng giá" className="flex flex-wrap gap-2">
            {budgetRanges.map((option) => (
              <button
                type="button"
                key={option.label}
                onClick={() => setRange(option)}
                aria-pressed={range === option}
                className="min-h-9 cursor-pointer rounded-full bg-(--store-soft) px-4 py-1.5 text-xs font-semibold text-(--store-muted) transition-colors hover:bg-(--store-soft-hover) aria-pressed:bg-(--store-primary) aria-pressed:text-white sm:min-h-7"
              >
                {option.label}
              </button>
            ))}
          </div>
        </SectionHeading>

        {range === budgetRanges[0] ? (
          <HomeProductResults request={request} emptyTitle="Chưa có sản phẩm để gợi ý">
            {(items) => {
              const suggestions = items.slice(cardsPerSection)
              const remaining = cardsPerSection - suggestions.length
              return <BudgetProductGrid items={[...suggestions, ...items.slice(0, remaining)]} />
            }}
          </HomeProductResults>
        ) : <FilteredBudgetProducts key={range.label} range={range} />}
      </section>
    </>
  )
}

function FilteredBudgetProducts({ range }: { range: (typeof budgetRanges)[number] }) {
  const load = useCallback(() => {
    const params = new URLSearchParams({ limit: String(cardsPerSection) })
    if (range.min) params.set('min_price', range.min)
    if (range.max) params.set('max_price', range.max)
    return api.catalogProducts(params)
  }, [range])
  const request = useBuyerRequest(load)
  return (
    <HomeProductResults request={request} emptyTitle="Chưa có sản phẩm trong khoảng giá này">
      {(items) => <BudgetProductGrid items={items} />}
    </HomeProductResults>
  )
}

function HomeProductResults({ request, emptyTitle, children }: {
  request: ReturnType<typeof useBuyerRequest<CatalogProductPage>>
  emptyTitle: string
  children: (items: CatalogProductCard[]) => ReactNode
}) {
  const { state, retry } = request
  if (state.status === 'loading') return <BuyerLoading label="Đang tải sản phẩm…" />
  if (state.status === 'error') return <BuyerRequestError message="Không tải được sản phẩm." retry={retry} />
  return state.data.items.length ? children(state.data.items) : <BuyerEmptyState title={emptyTitle} />
}

function BudgetProductGrid({ items }: { items: CatalogProductCard[] }) {
  return <ul className={productGridClass}>{items.map((product) => <HomeProductCard key={product.id} product={product} />)}</ul>
}

function HomeProductCard({ product, favorite, onFavorite }: { product: CatalogProductCard; favorite?: boolean; onFavorite?: () => void }) {
  return (
    <li className="group relative min-w-0 rounded-xl bg-white p-3 shadow-xs transition-shadow hover:shadow-md sm:p-4">
      <Link to={`/products/${product.id}`} className="flex h-full min-w-0 flex-col rounded-lg">
        <div className="mb-3 aspect-square overflow-hidden rounded-lg bg-(--store-soft) sm:mb-4">
          <ProductPhoto url={product.image_url} alt="" lazy cover />
        </div>
        <p className="truncate text-xs text-(--store-muted)">{product.shop.name}</p>
        <h3 className="mt-0.5 line-clamp-2 min-h-10 text-sm leading-5 font-semibold wrap-anywhere sm:min-h-12 sm:text-base sm:leading-6">{product.name}</h3>
        <div className="mt-auto flex flex-wrap items-center justify-between gap-x-2 gap-y-0.5 pt-2">
          <p className="text-base leading-6 font-semibold wrap-anywhere tabular-nums sm:text-xl sm:leading-7">{productPrice.format(product.price)}</p>
          <p className="text-xs text-(--store-muted)">{product.in_stock ? 'Còn hàng' : 'Hết hàng'}</p>
        </div>
      </Link>
      {onFavorite && <FavoriteProductButton name={product.name} pressed={favorite ?? false} toggle={onFavorite} />}
    </li>
  )
}
