export const BRAND = 'E-Market'

const logoWidths = {
  default: 'w-36',
  compact: 'w-28',
  auth: 'w-48 sm:w-56',
}

export function Logo({ light = false, variant = 'default' }: { light?: boolean; variant?: keyof typeof logoWidths }) {
  return (
    <img
      src="/logo.png"
      alt={BRAND}
      width={2172}
      height={724}
      className={`block h-auto max-w-full shrink-0 rounded-lg dark:bg-white ${logoWidths[variant]} ${light ? 'bg-white' : ''}`}
    />
  )
}
