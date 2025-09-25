import clsx from 'clsx'
import type { ReactNode } from 'react'

type ChipVariant = 'neutral' | 'accent' | 'subtle'

const VARIANT_MAP: Record<ChipVariant, string> = {
  neutral: 'bg-neutral-surfaceAlt text-neutral-text border border-neutral-borderLight',
  accent: 'bg-brand-primary/10 text-brand-primaryDark border border-brand-primary/20',
  subtle: 'bg-neutral-surface text-neutral-textMuted border border-transparent',
}

export type ChipProps = {
  children: ReactNode
  className?: string
  variant?: ChipVariant
}

export function Chip({ children, className, variant = 'neutral' }: ChipProps) {
  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1 rounded-badge px-2 py-0.5 text-[12px] font-medium leading-none',
        VARIANT_MAP[variant],
        className,
      )}
    >
      {children}
    </span>
  )
}

export default Chip
