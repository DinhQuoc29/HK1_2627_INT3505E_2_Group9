import { useCallback, useRef, useState, type FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { ApiError, api, type Cart, type CheckoutRequest, type CheckoutResult, type FieldError } from '../../shared/api/client'
import { useAuth } from '../../shared/auth/AuthContext'
import { Alert, Button, Spinner, TextField } from '../../shared/auth/components/ui'
import { BuyerStoreLayout } from '../BuyerStoreLayout'
import { CatalogError, catalogLink, productPrice } from '../catalog/catalogUi'
import { catalogErrorMessage, useCatalogRequest } from '../catalog/useCatalogRequest'

const panel = 'min-w-0 rounded-2xl border border-zinc-200 bg-white p-4 sm:p-6 dark:border-zinc-800 dark:bg-zinc-900'
type Attempt = { key: string; body: CheckoutRequest }
type Review = { cart: Cart } | { result: CheckoutResult }

// Chỉ lưu mã xác nhận để có thể tìm kết quả sau khi tải lại.
function readKey(storageKey: string): string | null {
  try { return sessionStorage.getItem(storageKey) } catch { return null }
}

function saveKey(storageKey: string, key: string | null) {
  try {
    if (key === null) sessionStorage.removeItem(storageKey)
    else sessionStorage.setItem(storageKey, key)
  } catch { /* Vẫn có thể thử lại trong trang khi trình duyệt chặn lưu trữ. */ }
}

function newKey(): string {
  const bytes = crypto.getRandomValues(new Uint8Array(16))
  return Array.from(bytes, (value) => value.toString(16).padStart(2, '0')).join('')
}

export default function BuyerCheckoutPage() {
  const { user } = useAuth()
  return user ? <CheckoutPage key={user.id} storageKey={`checkout:${user.id}`} name={user.full_name} /> : null
}

function CheckoutPage({ storageKey, name }: { storageKey: string; name: string }) {
  const load = useCallback(async (): Promise<Review> => {
    const key = readKey(storageKey)
    if (key) {
      try {
        const result = await api.recoverCheckout(key)
        saveKey(storageKey, null)
        return { result }
      } catch (error) {
        if (!(error instanceof ApiError && error.status === 404)) throw error
      }
    }
    return { cart: await api.cart() }
  }, [storageKey])
  const { state, retry } = useCatalogRequest(load)

  if (state.status === 'ready' && 'result' in state.data) {
    return <Navigate to={`/checkout/${state.data.result.id}`} replace />
  }

  return (
    <BuyerStoreLayout>
      <div className="mx-auto max-w-6xl space-y-5 px-4 py-7 sm:px-6 sm:py-10">
        <Link to="/cart" className={`inline-block ${catalogLink}`}>← Quay lại giỏ hàng</Link>
        <h1 className="text-3xl font-bold tracking-tight">Thanh toán</h1>
        {state.status === 'loading' && <Spinner label="Đang tải thông tin thanh toán…" />}
        {state.status === 'error' && (
          <CatalogError message={catalogErrorMessage(state.error, 'Không tải được thông tin thanh toán.')} retry={retry} />
        )}
        {state.status === 'ready' && 'cart' in state.data && (
          <ConfirmPurchase initial={state.data.cart} name={name} storageKey={storageKey} checkResult={retry} />
        )}
      </div>
    </BuyerStoreLayout>
  )
}

function ConfirmPurchase({ initial, name, storageKey, checkResult }: {
  initial: Cart
  name: string
  storageKey: string
  checkResult: () => void
}) {
  const navigate = useNavigate()
  const submitting = useRef(false)
  const [cart, setCart] = useState(initial)
  const [busy, setBusy] = useState(false)
  const [attempt, setAttempt] = useState<Attempt | null>(null)
  const [notice, setNotice] = useState('')
  const [fieldErrors, setFieldErrors] = useState<FieldError[]>([])
  const [previousPrices, setPreviousPrices] = useState<Record<string, number>>({})
  const [needsRefresh, setNeedsRefresh] = useState(false)
  const lines = cart.groups.flatMap(({ items }) => items)
  const blocked = lines.some((item) => !item.is_active || item.quantity > item.available_quantity)
  const tooExpensive = BigInt(cart.subtotal_vnd) > BigInt(Number.MAX_SAFE_INTEGER)

  async function refreshReview() {
    setNeedsRefresh(true)
    try {
      setCart(await api.cart())
      setNeedsRefresh(false)
    } catch {
      setNotice('Chưa tải được giỏ hàng mới. Hãy cập nhật lại trước khi xác nhận.')
    }
  }

  function openResult(result: CheckoutResult) {
    saveKey(storageKey, null)
    navigate(`/checkout/${result.id}`, { replace: true })
  }

  async function confirm(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (submitting.current || (!attempt && (blocked || tooExpensive || needsRefresh || !lines.length))) return
    const data = new FormData(event.currentTarget)
    const value = (key: string) => String(data.get(key) ?? '').trim()
    const current = attempt ?? {
      key: readKey(storageKey) ?? newKey(),
      body: {
        items: lines.map((item) => ({
          product_id: item.product_id, quantity: item.quantity, expected_unit_price: Number(item.unit_price_vnd),
        })),
        shipping: { name: value('name'), phone: value('phone'), address: value('address') },
      },
    }

    submitting.current = true
    setBusy(true)
    setNotice('')
    setFieldErrors([])
    saveKey(storageKey, current.key)
    try {
      openResult(await api.confirmCheckout(current.key, current.body))
    } catch (error) {
      if (error instanceof ApiError && error.slug === 'idempotency-key-conflict') {
        try {
          openResult(await api.recoverCheckout(current.key))
        } catch {
          setAttempt(current)
          setNotice('Chưa tải được kết quả của lần xác nhận trước. Vui lòng thử lại.')
        }
      } else if (!(error instanceof ApiError) || error.status === 0 || error.status >= 500) {
        setAttempt(current)
        setNotice('Chưa nhận được kết quả thanh toán. Bạn có thể thử lại cùng lần xác nhận này.')
      } else {
        saveKey(storageKey, null)
        setAttempt(null)
        setNotice(error.message)
        setFieldErrors(error.errors)
        if (error.slug === 'price-changed') {
          setPreviousPrices(Object.fromEntries(current.body.items.map((item) => [item.product_id, item.expected_unit_price])))
        }
        if (['price-changed', 'cart-changed', 'product-unavailable', 'insufficient-stock'].includes(error.slug)) {
          await refreshReview()
        }
      }
    } finally {
      submitting.current = false
      setBusy(false)
    }
  }

  if (!lines.length && !attempt) {
    return (
      <section className={`space-y-3 ${panel}`}>
        {notice && <Alert>{notice}</Alert>}
        <p>Giỏ hàng của bạn đang trống.</p>
        {readKey(storageKey) && <button type="button" onClick={checkResult} className={catalogLink}>Kiểm tra lại kết quả thanh toán</button>}
        <Link to="/products" className={`inline-block ${catalogLink}`}>Khám phá sản phẩm</Link>
      </section>
    )
  }

  const revised = lines.some((item) => item.product_id in previousPrices && Number(item.unit_price_vnd) !== previousPrices[item.product_id])
  const field = (key: string) => fieldErrors.find((error) => error.field === `shipping.${key}`)?.message
  const buttonLabel = attempt ? 'Thử xác nhận lại' : revised ? 'Xác nhận giá mới và thanh toán' : 'Xác nhận và thanh toán'

  return (
    <div className="space-y-4">
      {notice && <Alert tone={revised && !needsRefresh ? 'info' : 'error'}>{notice}</Alert>}
      {needsRefresh && !busy && (
        <button type="button" className={catalogLink} onClick={async () => {
          setBusy(true)
          await refreshReview()
          setBusy(false)
        }}>Cập nhật giỏ hàng</button>
      )}
      <div className="grid items-start gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <form id="checkout-confirm" onSubmit={confirm} className={`space-y-4 ${panel}`}>
          <h2 className="text-lg font-bold">Thông tin nhận hàng</h2>
          <TextField name="name" label="Họ tên người nhận" autoComplete="shipping name" maxLength={100} required defaultValue={name} error={field('name')} disabled={busy || !!attempt} />
          <TextField name="phone" label="Số điện thoại" type="tel" autoComplete="shipping tel" maxLength={20} required error={field('phone')} disabled={busy || !!attempt} />
          <TextField name="address" label="Địa chỉ nhận hàng" autoComplete="shipping street-address" maxLength={500} required error={field('address')} disabled={busy || !!attempt} />
        </form>
        <section aria-labelledby="checkout-summary" className={`space-y-4 ${panel}`}>
          <h2 id="checkout-summary" className="text-lg font-bold">Tóm tắt đơn hàng</h2>
          {cart.groups.map(({ shop, items }) => (
            <div key={shop.id} className="space-y-2 border-b border-zinc-200 pb-4 dark:border-zinc-800">
              <h3 className="break-words font-semibold">{shop.name}</h3>
              <ul className="space-y-2 text-sm text-zinc-600 dark:text-zinc-300">
                {items.map((item) => {
                  const old = previousPrices[item.product_id]
                  const changed = old !== undefined && old !== Number(item.unit_price_vnd)
                  const unitPrice = productPrice.format(BigInt(item.unit_price_vnd))
                  return (
                    <li key={item.product_id} className="flex flex-wrap justify-between gap-x-3 gap-y-1">
                      <span className="min-w-0 break-words">{item.name} × {item.quantity}</span>
                      <span className="font-medium">{productPrice.format(BigInt(item.line_total_vnd))}</span>
                      <span className={`w-full text-xs ${changed ? 'text-amber-800 dark:text-amber-300' : 'text-zinc-500 dark:text-zinc-400'}`}>
                        Đơn giá {changed && <><del>{productPrice.format(old)}</del> → </>}{unitPrice}
                      </span>
                      {(!item.is_active || item.quantity > item.available_quantity) && (
                        <span className="w-full text-amber-800 dark:text-amber-300">
                          {item.is_active ? `Còn ${item.available_quantity} món` : 'Đã ngừng bán'}
                        </span>
                      )}
                    </li>
                  )
                })}
              </ul>
            </div>
          ))}
          <p className="flex flex-wrap justify-between gap-2 font-bold">
            <span>Tổng thanh toán</span><span className="text-brand-700 dark:text-brand-100">{productPrice.format(BigInt(cart.subtotal_vnd))}</span>
          </p>
          <p className="text-sm text-zinc-600 dark:text-zinc-400">Thanh toán mô phỏng. Bạn không bị trừ tiền thật.</p>
          {blocked && <p className="text-sm text-amber-800 dark:text-amber-300">Hãy quay lại giỏ hàng để cập nhật các món thiếu hàng hoặc ngừng bán.</p>}
          {tooExpensive && <p className="text-sm text-amber-800 dark:text-amber-300">Tổng tiền vượt giới hạn. Hãy giảm số lượng trong giỏ hàng.</p>}
          <Button type="submit" form="checkout-confirm" loading={busy} disabled={!attempt && (blocked || tooExpensive || needsRefresh)}>
            {buttonLabel}
          </Button>
        </section>
      </div>
    </div>
  )
}
