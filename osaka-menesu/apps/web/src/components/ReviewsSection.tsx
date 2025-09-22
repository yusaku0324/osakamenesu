"use client"

import { useState, useTransition } from 'react'
import { ToastContainer, useToast } from './useToast'
import { Card } from './ui/Card'
import { Section } from './ui/Section'

export type ReviewItem = {
  id: string
  profile_id: string
  status: 'pending' | 'published' | 'rejected'
  score: number
  title?: string | null
  body: string
  author_alias?: string | null
  visited_at?: string | null
  created_at: string
  updated_at: string
}

type HighlightedReview = {
  review_id?: string | null
  title: string
  body: string
  score: number
  visited_at?: string | null
  author_alias?: string | null
}

type ReviewFormState = {
  score: number
  title: string
  body: string
  authorAlias: string
  visitedAt: string
}

type ReviewsSectionProps = {
  shopId: string
  averageScore?: number | null
  reviewCount?: number | null
  highlights?: HighlightedReview[] | null
  initialReviews: ReviewItem[]
  initialTotal: number
  initialPageSize: number
}

const SCORE_OPTIONS = [5, 4, 3, 2, 1]

function formatDateLabel(iso?: string | null): string | undefined {
  if (!iso) return undefined
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return iso
  return date.toLocaleDateString('ja-JP')
}

function renderStars(score: number): string {
  return '★'.repeat(score) + '☆'.repeat(Math.max(0, 5 - score))
}

export default function ReviewsSection({
  shopId,
  averageScore,
  reviewCount,
  highlights,
  initialReviews,
  initialTotal,
  initialPageSize,
}: ReviewsSectionProps) {
  const [reviews, setReviews] = useState<ReviewItem[]>(initialReviews)
  const [total, setTotal] = useState(initialTotal)
  const [page, setPage] = useState(1)
  const [isLoadingMore, startLoadTransition] = useTransition()
  const [formState, setFormState] = useState<ReviewFormState>({
    score: 5,
    title: '',
    body: '',
    authorAlias: '',
    visitedAt: '',
  })
  const [isSubmitting, startSubmitTransition] = useTransition()
  const { toasts, push, remove } = useToast()

  const effectiveAverage = averageScore ?? (reviewCount ? Number((reviews.reduce((sum, r) => sum + r.score, 0) / (reviews.length || 1)).toFixed(1)) : null)
  const effectiveCount = reviewCount ?? total
  const canLoadMore = reviews.length < total

  function handleChange<K extends keyof ReviewFormState>(key: K, value: ReviewFormState[K]) {
    setFormState(prev => ({ ...prev, [key]: value }))
  }

  async function loadMore() {
    startLoadTransition(async () => {
      const nextPage = page + 1
      try {
        const resp = await fetch(`/api/shops/${shopId}/reviews?page=${nextPage}&page_size=${initialPageSize}`, { cache: 'no-store' })
        if (!resp.ok) {
          push('error', 'レビューの読み込みに失敗しました。時間をおいて再度お試しください。')
          return
        }
        const data = (await resp.json()) as { total: number; items: ReviewItem[] }
        setReviews(prev => [...prev, ...data.items])
        setTotal(data.total)
        setPage(nextPage)
      } catch {
        push('error', 'ネットワークエラーが発生しました。')
      }
    })
  }

  async function submitReview() {
    if (!formState.body.trim()) {
      push('error', 'レビュー内容を入力してください。')
      return
    }
    startSubmitTransition(async () => {
      try {
        const payload = {
          score: formState.score,
          title: formState.title || undefined,
          body: formState.body,
          author_alias: formState.authorAlias || undefined,
          visited_at: formState.visitedAt || undefined,
        }
        const resp = await fetch(`/api/shops/${shopId}/reviews`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        })
        if (!resp.ok) {
          const data = await resp.json().catch(() => ({ detail: 'レビューの送信に失敗しました。' }))
          push('error', data?.detail || 'レビューの送信に失敗しました。')
          return
        }
        push('success', 'レビューを受け付けました。内容を確認後に公開されます。')
        setFormState({ score: 5, title: '', body: '', authorAlias: '', visitedAt: '' })
      } catch {
        push('error', 'ネットワークエラーが発生しました。')
      }
    })
  }

  return (
    <Section title="口コミ・レビュー" description="実際に利用した方からのお声を集めています。">
      <ToastContainer toasts={toasts} onDismiss={remove} />
      <div className="grid gap-6 lg:grid-cols-[3fr_2fr]">
        <div className="space-y-4">
          <Card className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-3xl font-semibold text-slate-800">
                  {effectiveAverage !== null ? effectiveAverage.toFixed(1) : '--'}
                </p>
                <p className="text-sm text-slate-500">平均評価</p>
              </div>
              <div className="text-right text-sm text-slate-500">
                <div>{renderStars(Math.round(effectiveAverage || 0))}</div>
                <div>{effectiveCount}件のレビュー</div>
              </div>
            </div>
            {highlights && highlights.length > 0 ? (
              <div className="space-y-3">
                {highlights.map((review, idx) => (
                  <div key={review.review_id || idx} className="rounded-md border border-slate-200 p-3">
                    <div className="flex items-center justify-between text-sm text-slate-600">
                      <span>{renderStars(review.score)}</span>
                      <span>{formatDateLabel(review.visited_at)}</span>
                    </div>
                    <h4 className="mt-1 text-sm font-semibold text-slate-700">{review.title}</h4>
                    <p className="mt-1 text-sm text-slate-600 whitespace-pre-wrap">{review.body}</p>
                    {review.author_alias ? (
                      <p className="mt-1 text-xs text-slate-400">投稿者: {review.author_alias}</p>
                    ) : null}
                  </div>
                ))}
              </div>
            ) : null}
          </Card>

          <Card className="space-y-4 p-4">
            <h3 className="text-lg font-semibold">最新の口コミ</h3>
            {reviews.length === 0 ? (
              <p className="text-sm text-slate-500">まだ口コミはありません。最初のレビューを投稿してみませんか？</p>
            ) : (
              <div className="space-y-4">
                {reviews.map((review) => (
                  <div key={review.id} className="border-b border-slate-100 pb-4 last:border-none last:pb-0">
                    <div className="flex items-center justify-between text-sm text-slate-600">
                      <span>{renderStars(review.score)}</span>
                      <span>{formatDateLabel(review.visited_at || review.created_at)}</span>
                    </div>
                    {review.title ? <h4 className="mt-1 text-sm font-semibold text-slate-700">{review.title}</h4> : null}
                    <p className="mt-1 text-sm text-slate-600 whitespace-pre-wrap">{review.body}</p>
                    {review.author_alias ? (
                      <p className="mt-1 text-xs text-slate-400">投稿者: {review.author_alias}</p>
                    ) : null}
                  </div>
                ))}
                {canLoadMore ? (
                  <button
                    onClick={loadMore}
                    disabled={isLoadingMore}
                    className="w-full rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {isLoadingMore ? '読み込み中...' : 'さらに読み込む'}
                  </button>
                ) : null}
              </div>
            )}
          </Card>
        </div>

        <Card className="space-y-4 p-4">
          <div>
            <h3 className="text-lg font-semibold">口コミを投稿する</h3>
            <p className="text-sm text-slate-500">お店の利用体験を教えてください。内容は確認後に公開されます。</p>
          </div>

          <div className="space-y-3">
            <label className="text-sm font-medium text-slate-700">
              評価
              <select
                value={formState.score}
                onChange={(e) => handleChange('score', Number(e.target.value))}
                className="mt-1 w-full rounded border px-3 py-2 text-sm"
              >
                {SCORE_OPTIONS.map((score) => (
                  <option key={score} value={score}>
                    {score} - {renderStars(score)}
                  </option>
                ))}
              </select>
            </label>

            <label className="text-sm font-medium text-slate-700">
              タイトル（任意）
              <input
                value={formState.title}
                onChange={(e) => handleChange('title', e.target.value)}
                className="mt-1 w-full rounded border px-3 py-2 text-sm"
                maxLength={160}
                placeholder="例: 技術も接客も大満足"
              />
            </label>

            <label className="text-sm font-medium text-slate-700">
              口コミ内容 *
              <textarea
                value={formState.body}
                onChange={(e) => handleChange('body', e.target.value)}
                className="mt-1 w-full rounded border px-3 py-2 text-sm"
                rows={5}
                maxLength={4000}
                placeholder="体験した内容やおすすめポイントなどを具体的にご記入ください。"
                required
              />
            </label>

            <label className="text-sm font-medium text-slate-700">
              投稿者名（任意）
              <input
                value={formState.authorAlias}
                onChange={(e) => handleChange('authorAlias', e.target.value)}
                className="mt-1 w-full rounded border px-3 py-2 text-sm"
                maxLength={80}
                placeholder="匿名でもOK"
              />
            </label>

            <label className="text-sm font-medium text-slate-700">
              来店日（任意）
              <input
                type="date"
                value={formState.visitedAt}
                onChange={(e) => handleChange('visitedAt', e.target.value)}
                className="mt-1 w-full rounded border px-3 py-2 text-sm"
              />
            </label>
          </div>

          <button
            onClick={submitReview}
            disabled={isSubmitting}
            className="w-full rounded-md bg-brand-primary px-4 py-2 text-sm font-semibold text-white shadow hover:bg-brand-primaryDark disabled:cursor-not-allowed disabled:opacity-70"
          >
            {isSubmitting ? '送信中...' : '口コミを投稿する'}
          </button>
          <p className="text-xs text-slate-400">
            投稿された内容は運営による確認後に公開されます。不適切な内容は非公開となる場合があります。
          </p>
        </Card>
      </div>
    </Section>
  )
}
