import Link from 'next/link'
import { cookies } from 'next/headers'

import { Card } from '@/components/ui/Card'
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

export default async function DashboardHomePage({
  params,
}: {
  params: { profileId: string }
}) {
  const cookieHeader = cookieHeaderFromStore()
  const result = await fetchDashboardShopProfile(params.profileId, { cookieHeader })

  if (result.status === 'unauthorized') {
    return (
      <main className="mx-auto max-w-4xl space-y-6 px-6 py-12">
        <h1 className="text-2xl font-semibold">店舗ダッシュボード</h1>
        <p className="text-neutral-600">
          ダッシュボードを表示するにはログインが必要です。マジックリンクでログインした後、このページを再読み込みしてください。
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
        <h1 className="text-2xl font-semibold">店舗ダッシュボード</h1>
        <p className="text-neutral-600">
          このプロフィールにアクセスする権限がありません。運営までお問い合わせください。
        </p>
      </main>
    )
  }

  if (result.status === 'not_found') {
    return (
      <main className="mx-auto max-w-4xl space-y-6 px-6 py-12">
        <h1 className="text-2xl font-semibold">店舗ダッシュボード</h1>
        <p className="text-neutral-600">指定されたプロフィールが見つかりませんでした。</p>
      </main>
    )
  }

  if (result.status === 'error') {
    return (
      <main className="mx-auto max-w-4xl space-y-6 px-6 py-12">
        <h1 className="text-2xl font-semibold">店舗ダッシュボード</h1>
        <p className="text-neutral-600">{result.message}</p>
      </main>
    )
  }

  const data = result.data

  return (
    <main className="mx-auto max-w-5xl space-y-8 px-6 py-12">
      <header className="space-y-2">
        <p className="text-sm text-neutral-500">プロフィール ID: {data.id}</p>
        <h1 className="text-3xl font-semibold tracking-tight">{data.name || '店舗ダッシュボード'}</h1>
        <p className="text-sm text-neutral-600">
          店舗ページの情報管理や予約通知の設定をまとめて行えます。右のメニューから編集したい項目を選んでください。
        </p>
      </header>

      <section className="grid gap-6 md:grid-cols-2">
        <Card className="p-6">
          <div className="space-y-2">
            <h2 className="text-xl font-semibold text-neutral-900">店舗プロフィールを編集</h2>
            <p className="text-sm text-neutral-600">
              基本情報・メニュー・在籍スタッフ・連絡先などの掲載内容を更新します。保存すると公開ページへ反映されます。
            </p>
            <Link
              href={`/dashboard/${data.id}/profile`}
              className="inline-flex items-center justify-center rounded-md bg-neutral-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-neutral-700"
            >
              プロフィール編集へ進む
            </Link>
          </div>
        </Card>

        <Card className="p-6">
          <div className="space-y-2">
            <h2 className="text-xl font-semibold text-neutral-900">予約通知の設定</h2>
            <p className="text-sm text-neutral-600">
              予約リクエスト受信時に通知を送るメール / LINE / Slack などのチャネルを管理します。宛先のテスト送信も可能です。
            </p>
            <Link
              href={`/dashboard/${data.id}/notifications`}
              className="inline-flex items-center justify-center rounded-md border border-neutral-300 px-4 py-2 text-sm font-semibold text-neutral-700 transition hover:bg-neutral-100"
            >
              通知設定へ進む
            </Link>
          </div>
        </Card>
      </section>
    </main>
  )
}
