const lastUpdatedFormatter = new Intl.DateTimeFormat('ja-JP', {
  month: 'short',
  day: 'numeric',
  weekday: 'short',
  hour: '2-digit',
  minute: '2-digit',
})

export type FormatLastUpdatedOptions = {
  prefix?: string
}

export function formatLastUpdated(
  value: string | number | Date | null | undefined,
  options: FormatLastUpdatedOptions = {},
): string | null {
  if (value == null) return null
  const date = value instanceof Date ? value : new Date(value)
  if (Number.isNaN(date.getTime())) return null
  const label = lastUpdatedFormatter.format(date)
  const prefix = options.prefix ?? '最終更新'
  return `${prefix} ${label}`
}

export { lastUpdatedFormatter }
