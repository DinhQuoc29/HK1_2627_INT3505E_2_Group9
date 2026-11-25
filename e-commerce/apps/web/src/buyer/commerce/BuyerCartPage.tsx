import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { ApiError, api, type Cart, type CartLine } from '../../shared/api/client'
import { Alert, Spinner, TextField } from '../../shared/auth/components/ui'
import { BuyerStoreLayout } from '../BuyerStoreLayout'
import { CatalogError, ProductPhoto, catalogLink, productPrice } from '../catalog/catalogUi'
import { catalogErrorMessage, useCatalogRequest } from '../catalog/useCatalogRequest'

const money = (amount: string) => productPrice.format(BigInt(amount))

export default function BuyerCartPage() {
  const { state, retry } = useCatalogRequest(api.cart)

  return (
    <BuyerStoreLayout>
      <div className="mx-auto max-w-7xl px-4 py-7 sm:px-6 sm:py-10">
        <h1 className="mb-6 text-3xl font-bold tracking-tight">Giỏ hàng</h1>
        {state.status === 'loading' && <Spinner label="Đang tải giỏ hàng…" />}
        {state.status === 'error' && (
          <CatalogError message={catalogErrorMessage(state.error, 'Không tải được giỏ hàng.')} retry={retry} />
        )}
        {state.status === 'ready' && <CartContents initial={state.data} />}
      </div>
    </BuyerStoreLayout>
  )
}

function CartContents({ initial }: { initial: Cart }) {
  const [cart, setCart] = useState(initial)
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState<{ tone: 'success' | 'error'; text: string }>()
  const hasUnavailable = cart.groups.some(({ items }) => items.some((item) => item.available_quantity < item.quantity))

  async function change(action: () => Promise<Cart>, success: string) {
    if (busy) return
    setBusy(true)
    setMessage(undefined)
    try {
      setCart(await action())
      setMessage({ tone: 'success', text: success })
    } catch (error) {
      setMessage({ tone: 'error', text: catalogErrorMessage(error, 'Không cập nhật được giỏ hàng.') })
      if (error instanceof ApiError && (error.status === 404 || error.status === 409)) {
        // Giá hoặc tồn kho có thể đã đổi trong lúc người mua đang xem.
        const latest = await api.cart().catch(() => null)
        if (latest) setCart(latest)
      }
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="space-y-4" aria-busy={busy}>
      {message && <Alert tone={message.tone}>{message.text}</Alert>}
      {cart.groups.length === 0 ? (
        <section className="rounded-2xl border border-dashed border-zinc-300 px-6 py-12 text-center dark:border-zinc-700">
          <h2 className="mb-3 text-lg font-semibold">Giỏ hàng của bạn đang trống</h2>
          <Link to="/products" className={`inline-block ${catalogLink}`}>Khám phá sản phẩm</Link>
        </section>
      ) : (
        <div className="grid items-start gap-5 lg:grid-cols-[minmax(0,1fr)_18rem]">
          <div className="space-y-4">
            {cart.groups.map(({ shop, items, subtotal_vnd }) => (
              <section key={shop.id} aria-labelledby={`shop-${shop.id}`} className="min-w-0 rounded-2xl border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900">
                <header className="flex flex-wrap items-baseline gap-x-3 gap-y-1 border-b border-zinc-200 px-4 py-4 sm:px-5 dark:border-zinc-800">
                  <h2 id={`shop-${shop.id}`} className="break-words text-lg font-bold">{shop.name}</h2>
                  <span className="text-sm text-zinc-500 dark:text-zinc-400">{shop.province.name}</span>
                </header>
                <ul className="divide-y divide-zinc-200 px-4 sm:px-5 dark:divide-zinc-800">
                  {items.map((item) => (
                    <CartItem
                      key={`${item.product_id}:${item.quantity}`}
                      item={item}
                      busy={busy}
                      save={(quantity) => change(() => api.changeCartItem(item.product_id, quantity), 'Đã cập nhật số lượng.')}
                      remove={() => change(() => api.removeCartItem(item.product_id), 'Đã xóa sản phẩm khỏi giỏ.')}
                    />
                  ))}
                </ul>
                <div className="flex flex-wrap justify-between gap-2 border-t border-zinc-200 px-4 py-3 text-sm sm:px-5 dark:border-zinc-800">
                  <span>Tạm tính của shop</span>
                  <strong>{money(subtotal_vnd)}</strong>
                </div>
              </section>
            ))}
          </div>
          <aside aria-label="Tóm tắt giỏ hàng" className="space-y-3 rounded-2xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
            <h2 className="text-lg font-bold">Tạm tính giỏ hàng</h2>
            <p className="break-words text-2xl font-bold text-brand-700 dark:text-brand-100">{money(cart.subtotal_vnd)}</p>
            {hasUnavailable && <p className="text-sm text-zinc-600 dark:text-zinc-400">Tạm tính chỉ gồm các món đang bán và đủ số lượng.</p>}
            {hasUnavailable ? (
              <p className="text-sm font-medium text-amber-800 dark:text-amber-300">Cập nhật hoặc xóa các món thiếu hàng trước khi thanh toán.</p>
            ) : (
              <Link to="/checkout" className="flex min-h-11 items-center justify-center rounded-xl bg-brand-600 px-4 text-sm font-semibold text-white hover:bg-brand-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-500">
                Tiến hành thanh toán
              </Link>
            )}
            <Link to="/products" className={`inline-block ${catalogLink}`}>Tiếp tục mua sắm</Link>
          </aside>
        </div>
      )}
    </div>
  )
}

function CartItem({ item, busy, save, remove }: {
  item: CartLine
  busy: boolean
  save: (quantity: number) => Promise<void>
  remove: () => Promise<void>
}) {
  let stockNotice = ''
  if (!item.is_active) stockNotice = 'Đã ngừng bán'
  else if (item.available_quantity === 0) stockNotice = 'Hết hàng'
  else if (item.available_quantity < item.quantity) stockNotice = `Chỉ còn ${item.available_quantity} món. Hãy giảm số lượng.`

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const quantity = Number(new FormData(event.currentTarget).get('quantity'))
    if (quantity !== item.quantity) void save(quantity)
  }

  return (
    <li className="grid grid-cols-[4rem_minmax(0,1fr)] gap-3 py-4 sm:grid-cols-[5rem_minmax(0,1fr)_auto]">
      <div className="aspect-square overflow-hidden rounded-lg bg-zinc-100 p-1 dark:bg-zinc-800">
        <ProductPhoto url={item.image_url} alt="" lazy />
      </div>
      <div className="min-w-0 space-y-1">
        <h3 className="break-words font-semibold">
          {item.is_active ? <Link to={`/products/${item.product_id}`} className="hover:underline">{item.name}</Link> : item.name}
        </h3>
        <p className="text-sm text-zinc-600 dark:text-zinc-400">{money(item.unit_price_vnd)} / món</p>
        <p className="break-words text-sm font-semibold">Thành tiền {money(item.line_total_vnd)}</p>
        {item.price_changed && <p className="text-sm text-amber-800 dark:text-amber-300">Giá đã thay đổi từ khi thêm vào giỏ.</p>}
        {stockNotice && <p className="text-sm text-amber-800 dark:text-amber-300">{stockNotice}</p>}
      </div>
      <div className="col-start-2 flex flex-wrap items-end gap-2 sm:col-start-auto">
        {item.available_quantity > 0 ? (
          <form onSubmit={submit} className="flex flex-wrap items-end gap-1">
            <TextField className="w-24" label="Số lượng" aria-label={`Số lượng của ${item.name}`} name="quantity" type="number" min={1} max={item.available_quantity} step={1} defaultValue={item.quantity} required disabled={busy} />
            <button type="submit" disabled={busy} className={`min-h-11 disabled:opacity-50 ${catalogLink}`}>Lưu</button>
          </form>
        ) : <p className="self-center text-sm text-zinc-600 dark:text-zinc-400">Số lượng {item.quantity}</p>}
        <button type="button" aria-label={`Xóa ${item.name} khỏi giỏ`} disabled={busy} onClick={() => void remove()} className="min-h-11 rounded-lg px-3 text-sm font-semibold text-red-700 hover:bg-red-50 focus-visible:outline-2 disabled:opacity-50 dark:text-red-300 dark:hover:bg-red-950">
          Xóa
        </button>
      </div>
    </li>
  )
}
