const shapes = {
  search: <><circle cx="10.8" cy="10.8" r="6" /><path d="m15 15 5 5" /></>,
  cart: <><path d="M2 3h3l3.2 12h10.2L21 6H6" /><circle cx="9" cy="20" r="1" /><circle cx="18" cy="20" r="1" /></>,
  person: <><circle cx="12" cy="8" r="3" /><path d="M5 19a5 5 0 0 1 5-5h4a5 5 0 0 1 5 5H5Z" /></>,
  chevron: <path d="m9 6 6 6-6 6" />,
  arrow: <path d="M4 12h15m-6-6 6 6-6 6" />,
  shoe: <path d="M3 9.5 7 4l3 2 1.5 4 3 3 4.2 1.5a3 3 0 0 1 2.3 3V20h-8L3 11V9.5Zm1 0L14 18h7M9.5 8.5 8 10m4.5 1.5L11 13" />,
  chair: <path d="M6 11V7a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v4M6 11a2 2 0 0 0-4 0v6a1 1 0 0 0 1 1h18a1 1 0 0 0 1-1v-6a2 2 0 0 0-4 0v3H6v-3Zm-2 7v2m16-2v2" />,
  watch: <><circle cx="12" cy="12" r="5" /><path d="m9 8 1-5h4l1 5m-6 8 1 5h4l1-5m-3-7v3l2 1" /></>,
  shirt: <path d="M8 4a4 4 0 0 0 8 0l5 3-2 4-3-1v10H8V10l-3 1-2-4 5-3Z" />,
  headphones: <path d="M3 14v-2a9 9 0 0 1 18 0v2M3 14a2 2 0 0 1 2-2h2v7H5a2 2 0 0 1-2-2v-3Zm18 0a2 2 0 0 0-2-2h-2v7h2a2 2 0 0 0 2-2v-3Z" />,
  leaf: <path d="M12 20C7 20 3 16 3 10a9 9 0 0 1 9 7 9 9 0 0 1 9-7c0 6-4 10-9 10Zm-3-8c0-3 1-6 3-8 2 2 3 5 3 8m-3 8v-3" />,
  book: <path d="M4 5h5a3 3 0 0 1 3 3v12a4 4 0 0 0-4-2H4V5Zm16 0h-5a3 3 0 0 0-3 3v12a4 4 0 0 1 4-2h4V5Z" />,
  grid: <path d="M4 4h6v6H4zm10 0h6v6h-6zM4 14h6v6H4zm10 0h6v6h-6z" />,
  heart: <path d="M12 20s-8.5-4.8-8.5-10.1a4.5 4.5 0 0 1 8.5-2 4.5 4.5 0 0 1 8.5 2C20.5 15.2 12 20 12 20Z" />,
}

export function StoreIcon({ name, className = 'size-6', filled = false }: { name: keyof typeof shapes; className?: string; filled?: boolean }) {
  return (
    <svg aria-hidden="true" className={`shrink-0 ${className}`} viewBox="0 0 24 24" fill={filled ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      {shapes[name]}
    </svg>
  )
}
