import SearchFilters from '@/components/SearchFilters'
import ShopCard, { type ShopHit } from '@/components/shop/ShopCard'
import { Badge } from '@/components/ui/Badge'
import { Section } from '@/components/ui/Section'
import { Card } from '@/components/ui/Card'
import { buildApiUrl, resolveApiBases } from '@/lib/api'

type FacetValue = {
  value: string
  label?: string | null
  count: number
  selected?: boolean | null
}

type Promotion = {
  label: string
  description?: string | null
  expires_at?: string | null
  highlight?: string | null
}

type Params = {
  q?: string
  area?: string
  service?: string
  body?: string
  today?: string
  price_min?: string
  price_max?: string
  price_band?: string
  ranking_badges?: string
  promotions_only?: string
  discounts_only?: string
  diaries_only?: string
  sort?: string
  page?: string
  page_size?: string
}

function toQueryString(p: Record<string, string | undefined>) {
  const q = Object.entries(p)
    .filter(([, v]) => v !== undefined && v !== '')
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v as string)}`)
    .join('&')
  return q ? `?${q}` : ''
}

type SearchResponse = {
  page: number
  page_size: number
  total: number
  results: ShopHit[]
  facets: Record<string, FacetValue[]>
  _error?: string
}

async function fetchProfiles(params: Params): Promise<SearchResponse> {
  const query = toQueryString({
    q: params.q,
    area: params.area,
    category: params.service,
    service_tags: params.body,
    open_now: params.today,
    price_min: params.price_min,
    price_max: params.price_max,
    price_band: params.price_band,
    ranking_badges: params.ranking_badges,
    promotions_only: params.promotions_only,
    discounts_only: params.discounts_only,
    diaries_only: params.diaries_only,
    sort: params.sort,
    page: params.page || '1',
    page_size: params.page_size || '12',
  })

  let lastErr: Error | null = null
  const targets = resolveApiBases()
  const endpoint = `/api/v1/shops${query}`

  for (const base of targets) {
    try {
      const res = await fetch(buildApiUrl(base, endpoint), { cache: 'no-store' })
      if (res.ok) {
        const data = await res.json()
        return {
          page: Number(data.page ?? params.page ?? 1),
          page_size: Number(data.page_size ?? params.page_size ?? 12),
          total: Number(data.total ?? 0),
          results: (data.results ?? data.hits ?? []) as ShopHit[],
          facets: (data.facets ?? {}) as Record<string, FacetValue[]>,
        }
      }
      lastErr = new Error(`search failed: ${res.status}`)
    } catch (err) {
      lastErr = err as Error
    }
  }

  return {
    page: Number(params.page || '1'),
    page_size: Number(params.page_size || '12'),
    total: 0,
    results: [],
    facets: {},
    _error: lastErr?.message || '検索に失敗しました',
  }
}

type SpotlightItem = {
  id: string
  title: string
  description: string
  href: string
}

function buildEditorialSpots(total: number): SpotlightItem[] {
  if (total === 0) return []
  return [
    {
      id: 'pr-feature-apply',
      title: '掲載をご検討の店舗さまへ',
      description: '抽選で上位表示のPR枠をご案内中。専任コンシェルジュがサポートします。',
      href: '/apply',
    },
    {
      id: 'pr-campaign',
      title: '季節キャンペーン受付中',
      description: 'GW・夏休みなど特集ページでの露出を強化。空枠わずかにつきお早めに。',
      href: '/apply',
    },
  ]
}

function buildHighlights(facets: Record<string, FacetValue[]>, hits: ShopHit[]) {
  const highlights: string[] = []

  const areas = [...(facets.area ?? [])]
    .sort((a, b) => (b.count ?? 0) - (a.count ?? 0))
    .slice(0, 3)
  if (areas.length) {
    highlights.push(`人気エリア: ${areas.map((a) => a.label || a.value).join(' / ')}`)
  }

  const services = [...(facets.service_type ?? [])]
    .sort((a, b) => (b.count ?? 0) - (a.count ?? 0))
    .slice(0, 2)
  if (services.length) {
    highlights.push(`主な業態: ${services.map((s) => s.label || s.value).join('・')}`)
  }

  const priceBands = [...(facets.price_band ?? [])]
    .sort((a, b) => (b.count ?? 0) - (a.count ?? 0))
    .slice(0, 2)
  if (priceBands.length) {
    highlights.push(`人気料金帯: ${priceBands.map((p) => p.label || p.value).join(' / ')}`)
  }

  const todayCount = hits.filter((h) => h.today_available).length
  if (todayCount) {
    highlights.push(`本日予約可能: ${todayCount}件`)
  }

  const priced = hits.filter((h) => h.min_price || h.max_price)
  if (priced.length) {
    const minAvg = Math.round(priced.reduce((sum, h) => sum + (h.min_price || 0), 0) / priced.length)
    const maxAvg = Math.round(priced.reduce((sum, h) => sum + (h.max_price || h.min_price || 0), 0) / priced.length)
    if (minAvg) {
      const intl = new Intl.NumberFormat('ja-JP')
      highlights.push(`予算目安: ¥${intl.format(minAvg)}〜¥${intl.format(Math.max(minAvg, maxAvg))}`)
    }
  }

  const rated = hits.filter((h) => typeof h.rating === 'number' && h.rating)
  if (rated.length) {
    const avg = rated.reduce((sum, h) => sum + (h.rating || 0), 0) / rated.length
    highlights.push(`平均評価 ${avg.toFixed(1)}★`)
  }

  const promotionLabels = hits
    .flatMap((h) => (Array.isArray(h.promotions) ? h.promotions : []))
    .map((promotion) => promotion?.label)
    .filter((label): label is string => Boolean(label))
  if (promotionLabels.length) {
    const unique = [...new Set(promotionLabels)].slice(0, 2)
    highlights.push(`開催中キャンペーン: ${unique.join(' / ')}`)
  }

  const promoShops = hits.filter((h) => h.has_promotions)
  if (!promotionLabels.length && promoShops.length) {
    highlights.push(`割引・キャンペーン掲載店舗: ${promoShops.length}件`)
  }

  const diaryShops = hits.filter((h) => h.has_diaries || (h.diary_count ?? 0) > 0)
  if (diaryShops.length) {
    const totalDiaries = diaryShops.reduce((sum, h) => sum + (h.diary_count || 0), 0)
    highlights.push(`写メ日記掲載店舗: ${diaryShops.length}件／公開数 ${totalDiaries}件`)
  }

  const rankingReasons = hits
    .map((h) => h.ranking_reason)
    .filter((reason): reason is string => Boolean(reason))
  if (rankingReasons.length) {
    highlights.push(`編集部ピックアップ: ${rankingReasons[0]}`)
  }

  return highlights
}

export default async function SearchPage({ searchParams }: { searchParams: Params }) {
  const data = await fetchProfiles(searchParams)
  const { page, page_size: pageSize, total, results, facets, _error } = data
  const hits = results ?? []
  const lastPage = Math.max(1, Math.ceil((total || 0) / (pageSize || 12)))
  const highlights = buildHighlights(facets, hits)
  const editorialSpots = buildEditorialSpots(total)

  type GridItem =
    | { kind: 'shop'; value: ShopHit }
    | { kind: 'spotlight'; value: SpotlightItem }

  const gridItems: GridItem[] = []
  const prSlots = [1, 8, 15]

  if (hits.length > 0) {
    let prIndex = 0
    hits.forEach((hit, idx) => {
      if (prSlots.includes(idx + 1) && prIndex < editorialSpots.length) {
        gridItems.push({ kind: 'spotlight', value: editorialSpots[prIndex] })
        prIndex += 1
      }
      gridItems.push({ kind: 'shop', value: hit })
    })
    while (gridItems.length < hits.length + editorialSpots.length && prIndex < editorialSpots.length) {
      gridItems.push({ kind: 'spotlight', value: editorialSpots[prIndex] })
      prIndex += 1
    }
  }

  const qp = (n: number) => {
    const entries = Object.entries(searchParams || {}).filter(([, v]) => v !== undefined && v !== null)
    const sp = new URLSearchParams(entries as [string, string][])
    sp.set('page', String(Math.min(Math.max(n, 1), lastPage)))
    return `/search?${sp.toString()}`
  }

  return (
    <main className="mx-auto max-w-6xl space-y-6 px-4 py-6">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight text-neutral-text">大阪メンエスを探す</h1>
        <p className="text-sm text-neutral-textMuted">
          CityHeaven の情報量と丁寧さをそのままに、メンエス選びに必要な情報を最短で届ける検索ページです。
        </p>
        {highlights.length ? (
          <div className="flex flex-wrap gap-2 pt-2">
            {highlights.map((item) => (
              <Badge key={item} variant="outline">
                {item}
              </Badge>
            ))}
          </div>
        ) : null}
      </header>

      {_error ? (
        <Card className="border-state-dangerBg bg-state-dangerBg/60 p-4 text-sm text-state-dangerText">
          {_error}
        </Card>
      ) : null}

      <div className="space-y-4">
        <SearchFilters init={searchParams} facets={facets} />
        <Section
          title={`検索結果 ${total}件`}
          subtitle={total ? `ページ ${page} / ${lastPage}（${pageSize}件ずつ表示）` : '条件を調整すると候補が表示されます'}
          actions={total ? <span className="text-xs text-neutral-textMuted">最新情報は毎日更新</span> : undefined}
          className="shadow-none border border-neutral-borderLight bg-neutral-surface"
        >
          {total === 0 ? (
            <div className="flex flex-col items-center justify-center gap-3 rounded-card border border-dashed border-neutral-borderLight p-8 text-center text-neutral-textMuted">
              <p className="text-base font-medium text-neutral-text">一致する店舗が見つかりませんでした</p>
              <p className="text-sm">
                キーワードを減らす・エリアを広げる・予算条件を調整するなど、条件を緩めて再検索してみてください。
              </p>
            </div>
          ) : (
            <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
              {(gridItems.length ? gridItems : hits.map((hit) => ({ kind: 'shop', value: hit })) ).map((item) =>
                item.kind === 'shop' ? (
                  <ShopCard key={item.value.id} hit={item.value} />
                ) : (
                  <a
                    key={item.value.id}
                    href={item.value.href}
                    className="block focus:outline-none"
                  >
                    <Card interactive className="h-full bg-gradient-to-br from-brand-primary/10 via-brand-primary/5 to-brand-secondary/10 p-6">
                      <Badge variant="brand" className="mb-3 w-fit">
                        PR
                      </Badge>
                      <h3 className="text-lg font-semibold text-neutral-text">{item.value.title}</h3>
                      <p className="mt-2 text-sm text-neutral-textMuted">{item.value.description}</p>
                      <span className="mt-6 inline-flex items-center gap-1 text-sm font-semibold text-brand-primaryDark">
                        くわしく見る
                        <span aria-hidden>→</span>
                      </span>
                    </Card>
                  </a>
                )
              )}
            </div>
          )}

          {total > 0 ? (
            <nav className="mt-6 flex flex-wrap items-center justify-between gap-3 border-t border-neutral-borderLight pt-4 text-sm">
              <div className="text-neutral-textMuted">
                {page} / {lastPage}ページ（{total}件）
              </div>
              <div className="flex items-center gap-2">
                {page > 1 ? (
                  <a href={qp(page - 1)} className="rounded-badge border border-neutral-borderLight px-3 py-1 hover:border-brand-primary hover:text-brand-primary">
                    前へ
                  </a>
                ) : (
                  <span className="rounded-badge border border-neutral-borderLight/70 px-3 py-1 text-neutral-textMuted/60">前へ</span>
                )}
                {page < lastPage ? (
                  <a href={qp(page + 1)} className="rounded-badge border border-neutral-borderLight px-3 py-1 hover:border-brand-primary hover:text-brand-primary">
                    次へ
                  </a>
                ) : (
                  <span className="rounded-badge border border-neutral-borderLight/70 px-3 py-1 text-neutral-textMuted/60">次へ</span>
                )}
              </div>
            </nav>
          ) : null}
        </Section>
      </div>
    </main>
  )
}
