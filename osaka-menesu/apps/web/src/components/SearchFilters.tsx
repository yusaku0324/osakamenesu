"use client"
import { useEffect, useMemo, useState, useTransition } from 'react'
import { usePathname, useRouter, useSearchParams } from 'next/navigation'

type FacetValue = {
  value: string
  label?: string | null
  count?: number
  selected?: boolean | null
}

type Facets = Record<string, FacetValue[] | undefined>
type Props = { init?: Record<string, any>, facets?: Facets }

const AREA_ORDER = [
  '難波/日本橋',
  '梅田',
  '心斎橋',
  '天王寺',
  '谷町九丁目',
  '堺筋本町',
  '京橋',
  '北新地',
  '本町',
  '南森町',
  '新大阪',
  '江坂',
  '堺',
]

export default function SearchFilters({ init, facets }: Props) {
  const router = useRouter()
  const pathname = usePathname()
  const sp = useSearchParams()
  const [isPending, startTransition] = useTransition()

  const [q, setQ] = useState<string>(init?.q || sp.get('q') || '')
  const [area, setArea] = useState<string>(init?.area || sp.get('area') || '')
  const [service, setService] = useState<string>(init?.service || sp.get('service') || '')
  const [body, setBody] = useState<string>(init?.body || sp.get('body') || '')
  const [today, setToday] = useState<boolean>((init?.today ?? sp.get('today')) === 'true')
  const [min, setMin] = useState<string>(init?.price_min || sp.get('price_min') || '')
  const [max, setMax] = useState<string>(init?.price_max || sp.get('price_max') || '')
  const [sort, setSort] = useState<string>(init?.sort || sp.get('sort') || '')

  function push() {
    const params = new URLSearchParams()
    if (q) params.set('q', q)
    if (area) params.set('area', area)
    if (service) params.set('service', service)
    if (body) params.set('body', body)
    if (today) params.set('today', 'true')
    if (min) params.set('price_min', min)
    if (max) params.set('price_max', max)
    if (sort) params.set('sort', sort)
    params.set('page', '1')
    startTransition(() => router.replace(`${pathname}?${params.toString()}`))
    try { localStorage.setItem('search.last', params.toString()) } catch {}
  }

  useEffect(() => {
    if (!sp.toString() && typeof window !== 'undefined') {
      const last = localStorage.getItem('search.last')
      if (last) router.replace(`${pathname}?${last}`)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const areaOptions = useMemo(() => {
    const facetList = facets?.area || []
    const items: Array<[string, string]> = facetList.length
      ? facetList.map(f => [f.value, f.label || f.value])
      : AREA_ORDER.map(k => [k, k])
    if (area && !items.some(([v]) => v === area)) items.unshift([area, area])
    return items
  }, [area, facets?.area])

  // price (per 60min) unit helpers: 0-10 万円を yen 数値文字列へ/から
  function toUnit(yen: string): string {
    const n = parseInt(yen ?? '0', 10)
    if (yen === '0' || n === 0) return '0'
    if (!yen || isNaN(n) || n < 0) return ''
    return n % 10000 === 0 ? String(n / 10000) : ''
  }
  function fromUnit(unit: string): string {
    if (unit === '0') return '0'
    const u = parseInt(unit ?? '0', 10)
    if (!unit || isNaN(u) || u <= 0) return ''
    return String(u * 10000)
  }
  const priceUnits = Array.from({ length: 10 }, (_, i) => String(i + 1))
  const minUnits = ['0', ...priceUnits]

  const fieldClass = 'w-full rounded-lg border border-neutral-borderLight bg-neutral-surface px-3 py-2 text-sm shadow-sm focus:border-brand-primary focus:outline-none focus:ring-2 focus:ring-brand-secondary/30'

  return (
    <section className="sticky top-14 z-20 grid gap-3 rounded-section border border-neutral-borderLight bg-neutral-surface/95 p-4 backdrop-blur supports-[backdrop-filter]:bg-neutral-surface/80 md:grid-cols-5">
      <input value={q} onChange={e=>setQ(e.target.value)} placeholder="キーワードを入力" className={`${fieldClass} md:col-span-2`} />
      <select value={area} onChange={e=>setArea(e.target.value)} className={fieldClass}>
        <option value="">エリア</option>
        {areaOptions.map(([value,label]) => (
          <option key={value} value={value}>{label}</option>
        ))}
      </select>
      <select value={service} onChange={e=>setService(e.target.value)} className={fieldClass}>
        <option value="">サービス形態</option>
        <option value="store">店舗型</option>
        <option value="dispatch">派遣型</option>
      </select>
      <input value={body} onChange={e=>setBody(e.target.value)} placeholder="こだわりキーワード (例: アロマ)" className={fieldClass} />
      <label className="flex items-center gap-2 rounded-lg border border-transparent bg-neutral-surfaceAlt px-3 py-2 text-sm text-neutral-text">
        <input type="checkbox" checked={today} onChange={e=>setToday(e.target.checked)} className="h-4 w-4" />
        本日出勤のみ
      </label>
      <div className="flex gap-2 md:col-span-2">
        <select value={toUnit(min)} onChange={e=>setMin(fromUnit(e.target.value))} className={fieldClass}>
          <option value="">最低料金 (万)</option>
          {minUnits.map(u => (<option key={u} value={u}>{u}万</option>))}
        </select>
        <select value={toUnit(max)} onChange={e=>setMax(fromUnit(e.target.value))} className={fieldClass}>
          <option value="">最高料金 (万)</option>
          {priceUnits.map(u => (<option key={u} value={u}>{u}万</option>))}
        </select>
      </div>
      <select value={sort} onChange={e=>setSort(e.target.value)} className={fieldClass}>
        <option value="">並び替え</option>
        <option value="ranking_weight:desc">注目順</option>
        <option value="price_min:asc">料金安い順</option>
        <option value="price_min:desc">料金高い順</option>
        <option value="today:desc">本日出勤優先</option>
      </select>
      <button onClick={push} className="rounded-lg bg-brand-primary px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-brand-primaryDark disabled:cursor-not-allowed disabled:opacity-50" disabled={isPending}>検索する</button>
    </section>
  )
}
