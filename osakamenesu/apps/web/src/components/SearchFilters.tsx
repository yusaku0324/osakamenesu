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

  const extractParam = (key: string): string => {
    const initValue = init?.[key]
    if (typeof initValue === 'string') return initValue
    if (Array.isArray(initValue) && initValue.length) return String(initValue[0])
    return sp.get(key) ?? ''
  }

  const extractList = (key: string): string[] => {
    const sources: string[] = []
    const initValue = init?.[key]
    if (typeof initValue === 'string') sources.push(initValue)
    else if (Array.isArray(initValue)) sources.push(...initValue.map(v => String(v)))
    sources.push(...sp.getAll(key))
    return sources
      .flatMap(v => String(v).split(','))
      .map(v => v.trim())
      .filter(Boolean)
  }

  const [q, setQ] = useState<string>(() => extractParam('q'))
  const [area, setArea] = useState<string>(() => extractParam('area'))
  const [service, setService] = useState<string>(() => extractParam('service'))
  const [body, setBody] = useState<string>(() => extractParam('body'))
  const [today, setToday] = useState<boolean>(() => extractParam('today') === 'true')
  const [priceBands, setPriceBands] = useState<string[]>(() => extractList('price_band'))
  const [rankingBadges, setRankingBadges] = useState<string[]>(() => extractList('ranking_badges'))
  const [promotionsOnly, setPromotionsOnly] = useState<boolean>(() => extractParam('promotions_only') === 'true')
  const [discountsOnly, setDiscountsOnly] = useState<boolean>(() => extractParam('discounts_only') === 'true')
  const [diariesOnly, setDiariesOnly] = useState<boolean>(() => extractParam('diaries_only') === 'true')
  const [sort, setSort] = useState<string>(() => extractParam('sort') || 'recommended')

  function push() {
    const params = new URLSearchParams()
    if (q) params.set('q', q)
    if (area) params.set('area', area)
    if (service) params.set('service', service)
    if (body) params.set('body', body)
    if (today) params.set('today', 'true')
    if (priceBands.length) params.set('price_band', priceBands.join(','))
    if (rankingBadges.length) params.set('ranking_badges', rankingBadges.join(','))
    if (promotionsOnly) params.set('promotions_only', 'true')
    if (discountsOnly) params.set('discounts_only', 'true')
    if (diariesOnly) params.set('diaries_only', 'true')
    if (sort && sort !== 'recommended') params.set('sort', sort)
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

  const serviceOptions = useMemo(() => {
    const facetList = facets?.service_type || []
    if (!facetList.length) return [
      ['store', '店舗型'],
      ['dispatch', '派遣型'],
    ]
    return facetList.map(f => [f.value, f.label || f.value])
  }, [facets?.service_type])

  const priceFacet = facets?.price_band || []
  const badgeFacet = facets?.ranking_badges || []
  const diariesFacetCount = (facets?.has_diaries || []).find((f) => f.value === 'true')?.count ?? 0

  const toggleValue = (list: string[], value: string): string[] => (
    list.includes(value) ? list.filter(v => v !== value) : [...list, value]
  )

  const fieldClass = 'w-full rounded-lg border border-neutral-borderLight bg-neutral-surface px-3 py-2 text-sm shadow-sm focus:border-brand-primary focus:outline-none focus:ring-2 focus:ring-brand-secondary/30'
  const chipClass = (active: boolean) => `inline-flex items-center gap-1 rounded-badge border px-3 py-1 text-sm transition ${active ? 'border-brand-primary bg-brand-primary text-white shadow-sm' : 'border-neutral-borderLight bg-neutral-surfaceAlt text-neutral-text'}`

  return (
    <section className="sticky top-14 z-20 space-y-3 rounded-section border border-neutral-borderLight bg-neutral-surface/95 p-4 backdrop-blur supports-[backdrop-filter]:bg-neutral-surface/80">
      <div className="grid gap-3 md:grid-cols-5">
        <input value={q} onChange={e=>setQ(e.target.value)} placeholder="キーワードを入力" className={`${fieldClass} md:col-span-2`} />
        <select value={area} onChange={e=>setArea(e.target.value)} className={fieldClass}>
          <option value="">エリア</option>
          {areaOptions.map(([value,label]) => (
            <option key={value} value={value}>{label}</option>
          ))}
        </select>
        <select value={service} onChange={e=>setService(e.target.value)} className={fieldClass}>
          <option value="">サービス形態</option>
          {serviceOptions.map(([value, label]) => (
            <option key={value} value={value}>{label}</option>
          ))}
        </select>
        <input value={body} onChange={e=>setBody(e.target.value)} placeholder="こだわりキーワード (例: アロマ)" className={fieldClass} />
        <label className="flex items-center gap-2 rounded-lg border border-transparent bg-neutral-surfaceAlt px-3 py-2 text-sm text-neutral-text">
          <input type="checkbox" checked={today} onChange={e=>setToday(e.target.checked)} className="h-4 w-4" />
          本日出勤のみ
        </label>
        <select value={sort} onChange={e=>setSort(e.target.value)} className={fieldClass}>
          <option value="recommended">おすすめ順</option>
          <option value="price_asc">料金が安い順</option>
          <option value="price_desc">料金が高い順</option>
          <option value="rating">クチコミ評価順</option>
          <option value="new">更新が新しい順</option>
        </select>
        <button onClick={push} className="rounded-lg bg-brand-primary px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-brand-primaryDark disabled:cursor-not-allowed disabled:opacity-50" disabled={isPending}>検索する</button>
      </div>

      {priceFacet.length ? (
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <span className="text-xs font-semibold uppercase tracking-wide text-neutral-textMuted">料金帯</span>
          {priceFacet.map((facet) => {
            const active = priceBands.includes(facet.value)
            return (
              <button
                type="button"
                key={facet.value}
                className={chipClass(active)}
                onClick={() => setPriceBands(prev => toggleValue(prev, facet.value))}
              >
                {facet.label || facet.value}
                {typeof facet.count === 'number' ? <span className="text-xs opacity-70">{facet.count}</span> : null}
              </button>
            )
          })}
        </div>
      ) : null}

      {badgeFacet.length ? (
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <span className="text-xs font-semibold uppercase tracking-wide text-neutral-textMuted">特集バッジ</span>
          {badgeFacet.map((facet) => {
            const active = rankingBadges.includes(facet.value)
            return (
              <button
                type="button"
                key={facet.value}
                className={chipClass(active)}
                onClick={() => setRankingBadges(prev => toggleValue(prev, facet.value))}
              >
                {facet.label || facet.value}
                {typeof facet.count === 'number' ? <span className="text-xs opacity-70">{facet.count}</span> : null}
              </button>
            )
          })}
        </div>
      ) : null}

      <div className="flex flex-wrap gap-3 text-sm text-neutral-text">
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            className="h-4 w-4"
            checked={promotionsOnly}
            onChange={(e) => setPromotionsOnly(e.target.checked)}
          />
          割引・キャンペーン実施中のみ
        </label>
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            className="h-4 w-4"
            checked={discountsOnly}
            onChange={(e) => setDiscountsOnly(e.target.checked)}
          />
          クーポン掲載あり
        </label>
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            className="h-4 w-4"
            checked={diariesOnly}
            onChange={(e) => setDiariesOnly(e.target.checked)}
          />
          写メ日記掲載あり{diariesFacetCount ? ` (${diariesFacetCount})` : ''}
        </label>
      </div>
    </section>
  )
}
