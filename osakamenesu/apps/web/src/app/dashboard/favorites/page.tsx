import Link from 'next/link'
import { cookies } from 'next/headers'

import { buildApiUrl, resolveApiBases } from '@/lib/api'

type FavoriteRecord = {
  shop_id: string
  created_at: string
}

type ShopSummary = {
  id: string
  name: string
  area?: string | null
  slug?: string | null
  min_price?: number | null
  max_price?: number | null
  address?: string | null
}

type FavoritesResult =
  | { status: 'ok'; favorites: FavoriteRecord[]; cookieHeader?: string }
  | { status: 'unauthorized' }
  | { status: 'error'; message: string }

const dateFormatter = new Intl.DateTimeFormat('ja-JP', {
  dateStyle: 'medium',
  timeStyle: 'short',
})

const currencyFormatter = new Intl.NumberFormat('ja-JP')

function serializeCookies(): string | undefined {
  const store = cookies()
  const entries = store.getAll()
  if (!entries.length) {
    return undefined
  }
  return entries.map((item) => `${item.name}=${item.value}`).join('; ')
}

async function fetchFavorites(): Promise<FavoritesResult> {
  const cookieHeader = serializeCookies()
  let lastError: Error | null = null

  for (const base of resolveApiBases()) {
    try {
      const res = await fetch(buildApiUrl(base, 'api/favorites'), {
        headers: cookieHeader ? { cookie: cookieHeader } : undefined,
        cache: 'no-store',
      })

      if (res.status === 401) {
        return { status: 'unauthorized' }
      }

      if (!res.ok) {
        lastError = new Error(`お気に入りの取得に失敗しました (${res.status})`)
        continue
      }

      const favorites = (await res.json()) as FavoriteRecord[]
      return { status: 'ok', favorites, cookieHeader }
    } catch (error) {
      lastError = error instanceof Error ? error : new Error('お気に入りの取得に失敗しました')
    }
  }

  return {
    status: 'error',
    message: lastError?.message ?? 'お気に入りの取得中にエラーが発生しました',
  }
}

async function fetchShopSummary(shopId: string, cookieHeader?: string): Promise<ShopSummary | null> {
  for (const base of resolveApiBases()) {
    try {
      const res = await fetch(buildApiUrl(base, `api/v1/shops/${shopId}`), {
        headers: cookieHeader ? { cookie: cookieHeader } : undefined,
        cache: 'no-store',
      })

      if (!res.ok) {
        continue
      }

      const data = await res.json()
      return {
        id: data.id ?? shopId,
        name: data.name ?? '名称未設定',
        area: data.area_name ?? data.area ?? null,
        slug: data.slug ?? null,
        min_price: data.price_min ?? null,
        max_price: data.price_max ?? null,
        address: data.address ?? null,
      }
    } catch (error) {
      continue
    }
  }

  return null
}

function formatPriceRange(min?: number | null, max?: number | null): string {
  if (!min && !max) return '—'
  if (min && max && min === max) {
    return `¥${currencyFormatter.format(min)}`
  }
  const minLabel = min ? `¥${currencyFormatter.format(min)}` : '—'
  const maxLabel = max ? `¥${currencyFormatter.format(max)}` : '—'
  return `${minLabel} 〜 ${maxLabel}`
}

export const dynamic = 'force-dynamic'
export const revalidate = 0

export default async function FavoritesDashboardPage() {
  const result = await fetchFavorites()

  if (result.status === 'unauthorized') {
    return (
      <main className="mx-auto max-w-4xl space-y-6 px-6 py-12">
        <h1 className="text-2xl font-semibold">お気に入り</h1>
        <p className="text-neutral-600">
          お気に入りを表示するにはログインが必要です。マジックリンクでログインした後、このページを再読み込みしてください。
        </p>
        <Link href="/" className="inline-flex rounded bg-black px-4 py-2 text-sm font-medium text-white">
          トップへ戻る
        </Link>
      </main>
    )
  }

  if (result.status === 'error') {
    return (
      <main className="mx-auto max-w-4xl space-y-6 px-6 py-12">
        <h1 className="text-2xl font-semibold">お気に入り</h1>
        <p className="text-neutral-600">{result.message}</p>
      </main>
    )
  }

  const cookieHeader = result.cookieHeader ?? serializeCookies()
  const summaries = await Promise.all(
    result.favorites.map(async (favorite) => {
      const summary = await fetchShopSummary(favorite.shop_id, cookieHeader)
      return { favorite, summary }
    })
  )

  return (
    <main className="mx-auto max-w-5xl space-y-8 px-6 py-12">
      <header className="space-y-2">
        <h1 className="text-3xl font-semibold tracking-tight">お気に入り</h1>
        <p className="text-sm text-neutral-600">ログイン中のアカウントで保存した店舗の一覧です。</p>
      </header>

      {summaries.length === 0 ? (
        <div className="rounded border border-dashed border-neutral-300 bg-neutral-100 p-8 text-center text-neutral-600">
          まだお気に入りの店舗がありません。検索から気になる店舗を追加してみてください。
        </div>
      ) : (
        <div className="overflow-x-auto rounded border border-neutral-200 bg-white shadow-sm">
          <table className="min-w-full divide-y divide-neutral-200 text-sm">
            <thead className="bg-neutral-50">
              <tr>
                <th scope="col" className="px-4 py-3 text-left font-medium text-neutral-600">
                  店舗
                </th>
                <th scope="col" className="px-4 py-3 text-left font-medium text-neutral-600">
                  エリア
                </th>
                <th scope="col" className="px-4 py-3 text-left font-medium text-neutral-600">
                  料金目安
                </th>
                <th scope="col" className="px-4 py-3 text-left font-medium text-neutral-600">
                  登録日時
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-100">
              {summaries.map(({ favorite, summary }) => {
                const href = summary ? (summary.slug ? `/profiles/${summary.slug}` : `/profiles/${summary.id}`) : undefined
                return (
                  <tr key={`${favorite.shop_id}-${favorite.created_at}`} className="hover:bg-neutral-50">
                    <td className="px-4 py-3">
                      {summary ? (
                        <Link href={href!} className="text-brand-primary hover:underline">
                          {summary.name}
                        </Link>
                      ) : (
                        <span className="text-neutral-500">{favorite.shop_id}</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-neutral-600">{summary?.area || '—'}</td>
                    <td className="px-4 py-3 text-neutral-600">
                      {formatPriceRange(summary?.min_price, summary?.max_price)}
                    </td>
                    <td className="px-4 py-3 text-neutral-500">
                      {dateFormatter.format(new Date(favorite.created_at))}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </main>
  )
}
