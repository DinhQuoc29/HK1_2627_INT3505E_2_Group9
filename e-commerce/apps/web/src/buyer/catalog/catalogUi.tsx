import { useState } from 'react'

export const productPrice = new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' })

export function ProductPhoto({ url, alt, lazy = false }: { url: string | null; alt: string; lazy?: boolean }) {
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
      className="h-full w-full object-contain"
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
