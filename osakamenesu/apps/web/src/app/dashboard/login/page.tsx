import Link from 'next/link'

import { Card } from '@/components/ui/Card'
import { MagicLinkRequestForm } from './MagicLinkRequestForm'

export const dynamic = 'force-dynamic'
export const revalidate = 0

export default function DashboardLoginPage() {
  return (
    <main className="mx-auto max-w-lg space-y-8 px-6 py-12">
      <header className="space-y-2 text-center">
        <h1 className="text-3xl font-semibold tracking-tight">ダッシュボードにログイン</h1>
        <p className="text-sm text-neutral-600">
          登録済みのメールアドレスにマジックリンクを送信します。リンクを開くと自動的にログインが完了します。
        </p>
      </header>

      <Card className="space-y-4 p-6">
        <MagicLinkRequestForm />
      </Card>

      <div className="text-center text-sm text-neutral-600">
        <p>リンクを開いた後はダッシュボードに戻り、店舗管理を開始できます。</p>
        <p className="mt-2">
          <Link href="/dashboard/favorites" className="text-brand-primary hover:underline">
            お気に入り一覧を見る
          </Link>
        </p>
      </div>
    </main>
  )
}
