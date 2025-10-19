import Link from 'next/link'
import { cookies } from 'next/headers'

import { ShopProfileEditor } from './ShopProfileEditor'
import { fetchDashboardShopProfile } from '@/lib/dashboard-shops'

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

export default async function DashboardShopProfilePage({
  params,
}: {
  params: { profileId: string }
}) {
  const cookieHeader = cookieHeaderFromStore()
  const result = await fetchDashboardShopProfile(params.profileId, { cookieHeader })

  if (result.status === 'unauthorized') {
    return (
      <main className="mx-auto max-w-4xl space-y-6 px-6 py-12">
        <h1 className="text-2xl font-semibold">店舗プロフィール編集</h1>
        <p className="text-neutral-600">
          店舗プロフィールを編集するにはログインが必要です。マジックリンクでログインした後、このページを再読み込みしてください。
        </p>
        <Link href="/" className="inline-flex rounded bg-black px-4 py-2 text-sm font-medium text-white">
          トップへ戻る
        </Link>
      </main>
    )
  }

  if (result.status === 'forbidden') {
    return (
      <main className="mx-auto max-w-4xl space-y-6 px-6 py-12">
        <h1 className="text-2xl font-semibold">店舗プロフィール編集</h1>
        <p className="text-neutral-600">
          このプロフィールを編集する権限がありません。運営までお問い合わせください。
        </p>
      </main>
    )
  }

  if (result.status === 'not_found') {
    return (
      <main className="mx-auto max-w-4xl space-y-6 px-6 py-12">
        <h1 className="text-2xl font-semibold">店舗プロフィール編集</h1>
        <p className="text-neutral-600">指定されたプロフィールが見つかりませんでした。</p>
      </main>
    )
  }

  if (result.status === 'error') {
    return (
      <main className="mx-auto max-w-4xl space-y-6 px-6 py-12">
        <h1 className="text-2xl font-semibold">店舗プロフィール編集</h1>
        <p className="text-neutral-600">{result.message}</p>
      </main>
    )
  }

  const data = result.data

  return (
    <main className="mx-auto max-w-5xl space-y-8 px-6 py-12">
      <header className="space-y-2">
        <p className="text-sm text-neutral-500">プロフィール ID: {data.id}</p>
        <h1 className="text-3xl font-semibold tracking-tight">店舗プロフィール編集</h1>
        <p className="text-sm text-neutral-600">
          店舗ページに表示される基本情報やメニュー、在籍スタッフを更新できます。入力内容を保存すると公開ページに反映されます。
        </p>
      </header>

      <ShopProfileEditor profileId={data.id} initialData={data} />

      <Link
        href={`/dashboard/${data.id}`}
        className="inline-flex rounded border border-neutral-300 px-4 py-2 text-sm font-medium text-neutral-700 transition hover:bg-neutral-100"
      >
        ダッシュボードトップに戻る
      </Link>
    </main>
  )
}
