import { useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { api, type Shop } from '../shared/api/client'
import { useAuth } from '../shared/auth/AuthContext'
import { AppShell } from '../shared/layout/AppShell'
import { Alert, Spinner } from '../shared/auth/components/ui'
import { describeError } from '../shared/auth/errors'

/** Trang shop của seller (sản phẩm và đơn hàng sẽ bổ sung ở các module sau). */
export default function SellerShopPage() {
  const { user } = useAuth()
  const [shop, setShop] = useState<Shop | null>(null)
  const [error, setError] = useState<string>()

  useEffect(() => {
    if (user?.role !== 'seller') return
    let cancelled = false
    api.myShop().then(
      (s) => { if (!cancelled) setShop(s) },
      (e) => { if (!cancelled) setError(describeError(e).message) },
    )
    return () => { cancelled = true }
  }, [user?.role])

  if (user?.role !== 'seller') return <Navigate to="/" replace />

  return (
    <AppShell>
        <h1 className="text-2xl font-bold tracking-tight">Kênh người bán</h1>
        {error && <Alert>{error}</Alert>}
        {!shop && !error && <Spinner label="Đang tải shop…" />}
        {shop && (
          <section aria-label="Thông tin shop" className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
            <h2 className="text-xl font-semibold tracking-tight">{shop.name}</h2>
            <dl className="mt-4 grid gap-4 text-sm sm:grid-cols-2">
              <div><dt className="text-zinc-500">Nơi bán</dt><dd className="mt-0.5 font-medium">{shop.province.name}</dd></div>
              <div><dt className="text-zinc-500">Mở shop từ</dt><dd className="mt-0.5 font-medium">{new Date(shop.created_at).toLocaleDateString('vi-VN')}</dd></div>
            </dl>
          </section>
        )}
    </AppShell>
  )
}
