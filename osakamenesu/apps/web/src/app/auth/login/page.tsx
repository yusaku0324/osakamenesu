import Link from 'next/link'

import { Card } from '@/components/ui/Card'
import { SiteMagicLinkRequestForm } from './SiteMagicLinkRequestForm'

export const dynamic = 'force-dynamic'
export const revalidate = 0

export default function SiteLoginPage() {
  return (
    <main className="mx-auto max-w-2xl space-y-8 px-6 py-12">
      <header className="space-y-3 text-center">
        <h1 className="text-3xl font-semibold tracking-tight">ログインしてお気に入りを管理</h1>
        <p className="text-sm text-neutral-600">
          登録済みのメールアドレスにマジックリンクを送信します。同じブラウザでリンクを開くとログインが完了し、お気に入り保存や予約フォームの入力を引き続きご利用いただけます。
        </p>
      </header>

      <Card className="space-y-6 p-6">
        <SiteMagicLinkRequestForm />
      </Card>

      <section className="space-y-2 rounded border border-neutral-200 bg-neutral-50 p-6 text-sm text-neutral-700">
        <h2 className="text-base font-semibold text-neutral-900">店舗担当者の方はこちら</h2>
        <p>
          掲載店舗の運用管理を行う場合はダッシュボード専用のログインページをご利用ください。
        </p>
        <div>
          <Link href="/dashboard/login" className="text-brand-primary hover:underline">
            ダッシュボードにログイン
          </Link>
        </div>
      </section>
    </main>
  )
}
