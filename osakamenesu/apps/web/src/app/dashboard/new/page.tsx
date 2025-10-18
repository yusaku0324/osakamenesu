import Link from 'next/link'
import { cookies } from 'next/headers'

import { Card } from '@/components/ui/Card'
import { ShopCreateForm } from './ShopCreateForm'

function cookieHeaderFromStore(): string | undefined {
  const store = cookies()
  const entries = store.getAll()
  if (!entries.length) {
    return undefined
  }
  return entries.map((entry) => `${entry.name}=${entry.value}`).join('; ')
}

export const dynamic = 'force-dynamic'
export const revalidate = 0

export default function DashboardNewShopPage() {
  const cookieHeader = cookieHeaderFromStore()

  return (
    <main className="mx-auto max-w-4xl space-y-8 px-6 py-12">
      <header className="space-y-2">
        <h1 className="text-3xl font-semibold tracking-tight">新しい店舗を追加</h1>
        <p className="text-sm text-neutral-600">
          店舗名やエリア、連絡先を登録すると公開ページとダッシュボード編集画面が利用できます。入力内容は後から編集できます。
        </p>
      </header>

      <Card className="border-neutral-borderLight/80 bg-white/95 p-6 shadow-sm">
        <ShopCreateForm cookieHeader={cookieHeader} />
      </Card>

      <div>
        <Link
          href="/dashboard/favorites"
          className="inline-flex rounded border border-neutral-300 px-4 py-2 text-sm font-medium text-neutral-700 transition hover:bg-neutral-100"
        >
          お気に入り一覧へ戻る
        </Link>
      </div>
    </main>
  )
}
