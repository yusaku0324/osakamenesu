"use client"
import { type FormEventHandler, useEffect, useMemo, useRef, useState, useTransition } from 'react'
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
  const spKey = sp.toString()
  const [isMobile, setIsMobile] = useState(false)
  const [showFilters, setShowFilters] = useState(true)

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
  const [station, setStation] = useState<string>(() => extractParam('station'))
  const [service, setService] = useState<string>(() => extractParam('service'))
  const [body, setBody] = useState<string>(() => extractParam('body'))
  const [today, setToday] = useState<boolean>(() => extractParam('today') === 'true')
  const [priceBands, setPriceBands] = useState<string[]>(() => extractList('price_band'))
  const [rankingBadges, setRankingBadges] = useState<string[]>(() => extractList('ranking_badges'))
  const [promotionsOnly, setPromotionsOnly] = useState<boolean>(() => extractParam('promotions_only') === 'true')
  const [discountsOnly, setDiscountsOnly] = useState<boolean>(() => extractParam('discounts_only') === 'true')
  const [diariesOnly, setDiariesOnly] = useState<boolean>(() => extractParam('diaries_only') === 'true')
  const [sort, setSort] = useState<string>(() => extractParam('sort') || 'recommended')
  const firstRender = useRef(true)

  useEffect(() => {
    if (typeof window === 'undefined') return
    const media = window.matchMedia('(max-width: 768px)')
    const applyMatch = (matches: boolean) => {
      setIsMobile(matches)
      if (!matches) setShowFilters(true)
    }
    applyMatch(media.matches)
    const listener = (event: MediaQueryListEvent) => applyMatch(event.matches)
    media.addEventListener('change', listener)
    return () => media.removeEventListener('change', listener)
  }, [])

  const scrollToResults = () => {
    if (typeof window === 'undefined') return
    requestAnimationFrame(() => {
      const el = document.getElementById('search-results')
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    })
  }

  function push() {
    const params = new URLSearchParams()
    if (q) params.set('q', q)
    if (area) params.set('area', area)
    if (station) params.set('station', station)
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
    startTransition(() => {
      router.replace(`${pathname}?${params.toString()}`)
      scrollToResults()
    })
    if (isMobile) setShowFilters(false)
    try { localStorage.setItem('search.last', params.toString()) } catch {}
  }

  function reset() {
    setQ('')
    setArea('')
    setStation('')
    setService('')
    setBody('')
    setToday(false)
    setPriceBands([])
    setRankingBadges([])
    setPromotionsOnly(false)
    setDiscountsOnly(false)
    setDiariesOnly(false)
    setSort('recommended')
    startTransition(() => {
      router.replace(pathname)
      scrollToResults()
    })
    if (isMobile) setShowFilters(false)
    try { localStorage.removeItem('search.last') } catch {}
  }

  useEffect(() => {
    setQ(extractParam('q'))
    setArea(extractParam('area'))
    setStation(extractParam('station'))
    setService(extractParam('service'))
    setBody(extractParam('body'))
    setToday(extractParam('today') === 'true')
    setPriceBands(extractList('price_band'))
    setRankingBadges(extractList('ranking_badges'))
    setPromotionsOnly(extractParam('promotions_only') === 'true')
    setDiscountsOnly(extractParam('discounts_only') === 'true')
    setDiariesOnly(extractParam('diaries_only') === 'true')
    setSort(extractParam('sort') || 'recommended')
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [spKey])

  useEffect(() => {
    if (!sp.toString() && typeof window !== 'undefined') {
      const last = localStorage.getItem('search.last')
      if (last) router.replace(`${pathname}?${last}`)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (firstRender.current) {
      firstRender.current = false
      return
    }
    if (isMobile) {
      setShowFilters(false)
      scrollToResults()
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [spKey, isMobile])

  const areaOptions = useMemo(() => {
    const facetList = facets?.area || []
    const items: Array<[string, string]> = facetList.length
      ? facetList.map(f => [f.value, f.label || f.value])
      : AREA_ORDER.map(k => [k, k])
    if (area && !items.some(([v]) => v === area)) items.unshift([area, area])
    return items
  }, [area, facets?.area])

  const stationOptions = useMemo(() => {
    const facetList = facets?.nearest_station || []
    const items: Array<[string, string]> = facetList.length
      ? facetList.map(f => [f.value, f.label || f.value])
      : []
    if (station && !items.some(([v]) => v === station)) items.unshift([station, station])
    return items
  }, [station, facets?.nearest_station])

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

  const onSubmit: FormEventHandler<HTMLFormElement> = (event) => {
    event.preventDefault()
    push()
  }

  return (
    <div className="relative space-y-2">
      {isMobile ? (
        <div className="flex items-center justify-between">
          <span className="text-sm font-semibold text-neutral-text">検索条件</span>
          <button
            type="button"
            onClick={() => setShowFilters(prev => !prev)}
            className="inline-flex items-center gap-1 rounded-badge border border-neutral-borderLight px-3 py-1 text-xs font-semibold text-neutral-text transition hover:border-brand-primary hover:text-brand-primary"
          >
            {showFilters ? '条件を閉じる' : '条件を開く'}
          </button>
        </div>
      ) : null}
      <form
        onSubmit={onSubmit}
        role="search"
        aria-label="店舗検索条件"
        className={`space-y-4 rounded-section border border-neutral-borderLight/70 bg-white/85 p-5 shadow-lg shadow-neutral-950/5 backdrop-blur supports-[backdrop-filter]:bg-white/70 ${isMobile ? '' : 'lg:sticky lg:top-16 lg:z-20'} ${isMobile && !showFilters ? 'border-none bg-transparent p-0 shadow-none backdrop-blur-none space-y-0' : ''}`}
        aria-busy={isPending}
      >
        <div className={isMobile && !showFilters ? 'hidden' : 'space-y-4'}>
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div className="space-y-1">
          <span className="text-xs font-semibold uppercase tracking-wide text-neutral-textMuted">検索条件</span>
          <p className="text-xs text-neutral-textMuted/80">気になる条件を組み合わせて、一覧をリアルタイムに更新します。</p>
        </div>
        <button
          type="button"
          onClick={reset}
          className="inline-flex items-center gap-1 rounded-badge border border-neutral-borderLight/80 px-3 py-1 text-xs font-semibold text-neutral-text transition hover:border-brand-primary hover:text-brand-primary"
          disabled={isPending}
        >
          条件をリセット
        </button>
      </header>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4 lg:gap-4 xl:grid-cols-5">
        <input
          value={q}
          onChange={e=>setQ(e.target.value)}
          placeholder="キーワードを入力"
          className={`${fieldClass} sm:col-span-2 lg:col-span-2 xl:col-span-2`}
        />
        <div className="flex flex-col gap-2 sm:col-span-2 lg:col-span-2 xl:col-span-1">
          <select value={area} onChange={e=>setArea(e.target.value)} className={fieldClass}>
            <option value="">エリア</option>
            {areaOptions.map(([value,label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
          <select value={station} onChange={e=>setStation(e.target.value)} className={fieldClass}>
            <option value="">駅を選択</option>
            {stationOptions.map(([value,label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
        </div>
        <select value={service} onChange={e=>setService(e.target.value)} className={`${fieldClass} sm:col-span-2 lg:col-span-1`}>
          <option value="">サービス形態</option>
          {serviceOptions.map(([value, label]) => (
            <option key={value} value={value}>{label}</option>
          ))}
        </select>
        <input
          value={body}
          onChange={e=>setBody(e.target.value)}
          placeholder="こだわりキーワード (例: アロマ)"
          className={`${fieldClass} sm:col-span-2 lg:col-span-2 xl:col-span-2`}
        />
        <label className="flex items-center gap-2 rounded-lg border border-neutral-borderLight/70 bg-neutral-surfaceAlt px-3 py-2 text-sm text-neutral-text sm:col-span-2 lg:col-span-1">
          <input type="checkbox" checked={today} onChange={e=>setToday(e.target.checked)} className="h-4 w-4" />
          本日出勤のみ
        </label>
        <select value={sort} onChange={e=>setSort(e.target.value)} className={`${fieldClass} sm:col-span-2 lg:col-span-1`}>
          <option value="recommended">おすすめ順</option>
          <option value="price_asc">料金が安い順</option>
          <option value="price_desc">料金が高い順</option>
          <option value="rating">クチコミ評価順</option>
          <option value="new">更新が新しい順</option>
        </select>
        <button
          type="submit"
          className="inline-flex items-center justify-center rounded-lg bg-brand-primary px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-brand-primaryDark disabled:cursor-not-allowed disabled:opacity-50 sm:col-span-2 lg:col-span-1 lg:w-full xl:w-auto"
          disabled={isPending}
        >
          {isPending ? '更新中…' : '検索する'}
        </button>
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
        </div>
      </form>
    </div>
  )
}
