import { useState, type FormEvent } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { api } from '../../shared/api/client'
import { useAuth } from '../../shared/auth/AuthContext'
import { Alert, Button, TextField } from '../../shared/auth/components/ui'
import { catalogErrorMessage } from '../catalog/useCatalogRequest'
import { catalogLink } from '../catalog/catalogUi'

export function AddToCart({ productId, inStock }: { productId: string; inStock: boolean }) {
  const { status, user } = useAuth()
  const { pathname, search } = useLocation()
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState<{ tone: 'success' | 'error'; text: string }>()

  if (!inStock || status === 'loading' || (user && user.role !== 'buyer')) return null
  if (!user) {
    return (
      <Link to="/login" state={{ from: pathname + search }} className={`inline-block ${catalogLink}`}>
        Đăng nhập để thêm vào giỏ
      </Link>
    )
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (busy) return
    const quantity = Number(new FormData(event.currentTarget).get('quantity'))
    setBusy(true)
    setMessage(undefined)
    try {
      await api.addCartItem(productId, quantity)
      setMessage({ tone: 'success', text: 'Đã thêm sản phẩm vào giỏ hàng.' })
    } catch (error) {
      setMessage({ tone: 'error', text: catalogErrorMessage(error, 'Không thể thêm sản phẩm vào giỏ.') })
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="space-y-3">
      <form onSubmit={submit} className="flex flex-wrap items-end gap-3">
        <TextField className="w-24" label="Số lượng" name="quantity" type="number" min={1} max={2_147_483_647} step={1} defaultValue={1} required disabled={busy} />
        <div><Button type="submit" loading={busy}>Thêm vào giỏ</Button></div>
      </form>
      {message && (
        <Alert tone={message.tone}>
          {message.text}
          {message.tone === 'success' && <Link to="/cart" className="ml-2 font-semibold underline">Xem giỏ hàng</Link>}
        </Alert>
      )}
    </div>
  )
}
