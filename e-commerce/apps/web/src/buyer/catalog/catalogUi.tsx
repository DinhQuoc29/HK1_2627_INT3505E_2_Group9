import { useEffect, useState } from 'react'
import { StoreIcon } from '../../shared/layout/StoreIcon'

export const productPrice = new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' })

const favoritesKey = 'e-market:favorite-products'

export function useProductFavorites() {
  const [favorites, setFavorites] = useState<string[]>(() => {
    try {
      const saved: unknown = JSON.parse(localStorage.getItem(favoritesKey) ?? '[]')
      return Array.isArray(saved) ? saved.filter((value): value is string => typeof value === 'string') : []
    } catch {
      return []
    }
  })

  useEffect(() => {
    try {
      localStorage.setItem(favoritesKey, JSON.stringify(favorites))
    } catch {
      // Keep the current selection when the browser restricts local storage.
    }
  }, [favorites])

  function toggleFavorite(id: string) {
    setFavorites((saved) => saved.includes(id) ? saved.filter((item) => item !== id) : [...saved, id])
  }

  return { favorites, toggleFavorite }
}

export function FavoriteProductButton({ name, pressed, toggle }: { name: string; pressed: boolean; toggle: () => void }) {
  return (
    <button
      type="button"
      aria-label={`Yêu thích ${name}`}
      aria-pressed={pressed}
      onClick={toggle}
      className="absolute top-5 right-5 grid size-8 cursor-pointer place-items-center rounded-full bg-white/95 text-(--store-muted) shadow-xs backdrop-blur-sm transition-colors hover:text-(--store-primary) aria-pressed:text-(--store-primary) sm:top-7 sm:right-7"
    >
      <StoreIcon name="heart" className="size-[18px]" filled={pressed} />
    </button>
  )
}

export function ProductPhoto({ url, alt, lazy = false, cover = false }: { url: string | null; alt: string; lazy?: boolean; cover?: boolean }) {
  const [failedUrl, setFailedUrl] = useState<string | null>(null)
  if (!url || url === failedUrl) {
    return <div className="grid h-full w-full place-items-center p-2 text-center text-xs text-zinc-500">Không có ảnh</div>
  }
  return (
    <img
      src={url}
      alt={alt}
      loading={lazy ? 'lazy' : undefined}
      referrerPolicy="no-referrer"
      onError={() => setFailedUrl(url)}
      className={`h-full w-full ${cover ? 'object-cover transition-transform duration-300 group-hover:scale-105' : 'object-contain'}`}
    />
  )
}

export function Availability({ inStock }: { inStock: boolean }) {
  return (
    <span className={`inline-flex items-center gap-1.5 text-sm font-medium ${inStock ? 'text-emerald-700 dark:text-emerald-400' : 'text-zinc-500 dark:text-zinc-400'}`}>
      <span aria-hidden className="size-1.5 rounded-full bg-current" />
      {inStock ? 'Còn hàng' : 'Hết hàng'}
    </span>
  )
}
