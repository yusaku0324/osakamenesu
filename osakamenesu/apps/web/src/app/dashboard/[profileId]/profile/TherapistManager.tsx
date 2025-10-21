"use client"

import { FormEvent, useMemo, useState } from 'react'

import { Card } from '@/components/ui/Card'
import {
  type DashboardTherapistSummary,
  type DashboardTherapistDetail,
  type DashboardTherapistListResult,
  type DashboardTherapistMutationResult,
  type DashboardTherapistDeleteResult,
  createDashboardTherapist,
  deleteDashboardTherapist,
  fetchDashboardTherapist,
  reorderDashboardTherapists,
  summarizeTherapist,
  updateDashboardTherapist,
} from '@/lib/dashboard-therapists'

type ToastFn = (type: 'success' | 'error', message: string) => void

type Props = {
  profileId: string
  initialItems: DashboardTherapistSummary[]
  initialError?: string | null
  onToast: ToastFn
}

type TherapistFormMode = 'create' | 'edit'

type TherapistFormValues = {
  name: string
  alias: string
  headline: string
  biography: string
  specialties: string
  qualifications: string
  experienceYears: string
  photoUrls: string
  status: DashboardTherapistSummary['status']
  isBookingEnabled: boolean
}

type TherapistFormState = {
  mode: TherapistFormMode
  therapistId?: string
  updatedAt?: string
  values: TherapistFormValues
}

const STATUS_LABELS: Record<DashboardTherapistSummary['status'], string> = {
  draft: '下書き',
  published: '公開中',
  archived: 'アーカイブ',
}

const DEFAULT_FORM_VALUES: TherapistFormValues = {
  name: '',
  alias: '',
  headline: '',
  biography: '',
  specialties: '',
  qualifications: '',
  experienceYears: '',
  photoUrls: '',
  status: 'draft',
  isBookingEnabled: true,
}

function sortTherapists(items: DashboardTherapistSummary[]): DashboardTherapistSummary[] {
  return [...items].sort((a, b) => {
    if (a.display_order === b.display_order) {
      return a.updated_at.localeCompare(b.updated_at)
    }
    return a.display_order - b.display_order
  })
}

function parseCommaSeparated(value: string): string[] {
  return value
    .split(/[\n,]/)
    .map((segment) => segment.trim())
    .filter((segment, index, self) => segment.length > 0 && self.indexOf(segment) === index)
}

function detailToForm(detail: DashboardTherapistDetail): TherapistFormValues {
  return {
    name: detail.name ?? '',
    alias: detail.alias ?? '',
    headline: detail.headline ?? '',
    biography: detail.biography ?? '',
    specialties: Array.isArray(detail.specialties) ? detail.specialties.join(', ') : '',
    qualifications: Array.isArray(detail.qualifications) ? detail.qualifications.join(', ') : '',
    experienceYears:
      typeof detail.experience_years === 'number' && Number.isFinite(detail.experience_years)
        ? String(detail.experience_years)
        : '',
    photoUrls: Array.isArray(detail.photo_urls) ? detail.photo_urls.join('\n') : '',
    status: detail.status,
    isBookingEnabled: Boolean(detail.is_booking_enabled),
  }
}

function toErrorMessage(
  result: DashboardTherapistListResult | DashboardTherapistMutationResult | DashboardTherapistDeleteResult,
  fallback: string
): string {
  if ('message' in result && typeof result.message === 'string' && result.message.trim().length > 0) {
    return result.message
  }
  return fallback
}

export function TherapistManager({ profileId, initialItems, initialError, onToast }: Props) {
  const [therapists, setTherapists] = useState<DashboardTherapistSummary[]>(sortTherapists(initialItems))
  const [error, setError] = useState<string | null>(initialError ?? null)
  const [formState, setFormState] = useState<TherapistFormState | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isLoadingDetail, setIsLoadingDetail] = useState(false)

  const hasTherapists = therapists.length > 0

  function openCreateForm() {
    setFormState({
      mode: 'create',
      values: { ...DEFAULT_FORM_VALUES },
    })
  }

  async function openEditForm(therapistId: string) {
    setIsLoadingDetail(true)
    const result = await fetchDashboardTherapist(profileId, therapistId)
    setIsLoadingDetail(false)

    switch (result.status) {
      case 'success': {
        setFormState({
          mode: 'edit',
          therapistId,
          updatedAt: result.data.updated_at,
          values: detailToForm(result.data),
        })
        break
      }
      case 'not_found': {
        onToast('error', 'セラピストが見つかりませんでした。再読み込みしてください。')
        break
      }
      case 'unauthorized':
      case 'forbidden': {
        onToast('error', 'セラピスト情報を取得する権限がありません。')
        break
      }
      default: {
        onToast('error', toErrorMessage(result, 'セラピスト情報の取得に失敗しました。'))
      }
    }
  }

  function closeForm() {
    setFormState(null)
  }

  function handleValuesChange<T extends keyof TherapistFormValues>(key: T, value: TherapistFormValues[T]) {
    setFormState((prev) => {
      if (!prev) return prev
      return {
        ...prev,
        values: {
          ...prev.values,
          [key]: value,
        },
      }
    })
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!formState) return

    const values = formState.values
    const trimmedName = values.name.trim()
    if (!trimmedName) {
      onToast('error', 'セラピスト名を入力してください。')
      return
    }

    const payloadSpecialties = parseCommaSeparated(values.specialties)
    const payloadQualifications = parseCommaSeparated(values.qualifications)
    const photoUrls = values.photoUrls
      .split(/\n/)
      .map((line) => line.trim())
      .filter(Boolean)

    const experienceYears = values.experienceYears.trim()
    const experienceYearsNumber = experienceYears ? Number(experienceYears) : undefined

    const sharedFields = {
      alias: values.alias.trim() || undefined,
      headline: values.headline.trim() || undefined,
      biography: values.biography.trim() || undefined,
      specialties: payloadSpecialties.length ? payloadSpecialties : undefined,
      qualifications: payloadQualifications.length ? payloadQualifications : undefined,
      experience_years:
        experienceYearsNumber !== undefined && Number.isFinite(experienceYearsNumber)
          ? Math.max(0, Math.round(experienceYearsNumber))
          : undefined,
      photo_urls: photoUrls.length ? photoUrls : undefined,
      is_booking_enabled: Boolean(values.isBookingEnabled),
    }

    setIsSubmitting(true)
    try {
      if (formState.mode === 'create') {
        const result = await createDashboardTherapist(profileId, {
          name: trimmedName,
          ...sharedFields,
        })
        if (result.status === 'success') {
          setTherapists((prev) => sortTherapists([...prev, summarizeTherapist(result.data)]))
          setError(null)
          onToast('success', 'セラピストを追加しました。')
          closeForm()
        } else if (result.status === 'validation_error') {
          onToast('error', '入力内容に誤りがあります。確認してください。')
        } else if (result.status === 'unauthorized' || result.status === 'forbidden') {
          onToast('error', 'セラピストを追加する権限がありません。')
        } else {
          onToast('error', toErrorMessage(result, 'セラピストの追加に失敗しました。'))
        }
      } else {
        const result = await updateDashboardTherapist(profileId, formState.therapistId!, {
          updated_at: formState.updatedAt!,
          name: trimmedName,
          status: values.status,
          ...sharedFields,
        })
        if (result.status === 'success') {
          setTherapists((prev) =>
            sortTherapists(
              prev.map((item) =>
                item.id === result.data.id ? summarizeTherapist(result.data) : item
              )
            )
          )
          setError(null)
          onToast('success', 'セラピスト情報を更新しました。')
          closeForm()
        } else if (result.status === 'conflict') {
          onToast('error', '他のユーザーによって更新されました。再読み込みしてください。')
        } else if (result.status === 'validation_error') {
          onToast('error', '入力内容に誤りがあります。確認してください。')
        } else if (result.status === 'not_found') {
          onToast('error', 'セラピストが見つかりませんでした。')
        } else if (result.status === 'unauthorized' || result.status === 'forbidden') {
          onToast('error', 'セラピストを更新する権限がありません。')
        } else {
          onToast('error', toErrorMessage(result, 'セラピストの更新に失敗しました。'))
        }
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  async function handleDelete(therapistId: string) {
    const target = therapists.find((item) => item.id === therapistId)
    if (!target) return
    if (!window.confirm(`「${target.name}」を削除しますか？この操作は取り消せません。`)) {
      return
    }
    const result = await deleteDashboardTherapist(profileId, therapistId)
    if (result.status === 'success') {
      setTherapists((prev) => prev.filter((item) => item.id !== therapistId))
      onToast('success', 'セラピストを削除しました。')
    } else if (result.status === 'unauthorized' || result.status === 'forbidden') {
      onToast('error', 'セラピストを削除する権限がありません。')
    } else if (result.status === 'not_found') {
      onToast('error', 'セラピストが見つかりませんでした。')
    } else {
      onToast('error', toErrorMessage(result, 'セラピストの削除に失敗しました。'))
    }
  }

  async function persistOrder(next: DashboardTherapistSummary[], previous: DashboardTherapistSummary[]) {
    const payload = {
      items: next.map((item, index) => ({
        therapist_id: item.id,
        display_order: index * 10,
      })),
    }
    const result = await reorderDashboardTherapists(profileId, payload)
    if (result.status === 'success') {
      setTherapists(sortTherapists(result.data))
      setError(null)
      onToast('success', '並び順を更新しました。')
    } else if (result.status === 'unauthorized' || result.status === 'forbidden') {
      onToast('error', '並び順を変更する権限がありません。')
      setTherapists([...previous])
    } else if (result.status === 'not_found') {
      onToast('error', 'セラピストが見つかりませんでした。')
      setTherapists([...previous])
    } else {
      onToast('error', toErrorMessage(result, '並び順の変更に失敗しました。'))
      setTherapists([...previous])
    }
  }

  async function handleMove(index: number, direction: 1 | -1) {
    const targetIndex = index + direction
    if (targetIndex < 0 || targetIndex >= therapists.length) {
      return
    }
    const previous = [...therapists]
    const next = [...therapists]
    const [removed] = next.splice(index, 1)
    next.splice(targetIndex, 0, removed)
    setTherapists(next)
    await persistOrder(next, previous)
  }

  const statusOptions = useMemo(
    () =>
      Object.entries(STATUS_LABELS).map(([value, label]) => ({
        value: value as DashboardTherapistSummary['status'],
        label,
      })),
    []
  )

  return (
    <Card className="space-y-6 p-6">
      <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
        <div className="space-y-2">
          <h2 className="text-xl font-semibold">在籍セラピスト管理</h2>
          <p className="text-sm text-neutral-600">
            セラピストのプロフィールを追加・更新し、公開状態や表示順を管理します。公開中に設定すると店舗ページに表示されます。
          </p>
          {error ? <p className="text-sm text-red-600">{error}</p> : null}
        </div>
        <button
          type="button"
          onClick={openCreateForm}
          className="inline-flex items-center rounded-md bg-neutral-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-neutral-700"
        >
          新しいセラピストを追加
        </button>
      </div>

      <div className="space-y-4">
        {hasTherapists ? (
          therapists.map((therapist, index) => (
            <div
              key={therapist.id}
              className="flex flex-col gap-3 rounded-lg border border-neutral-200 bg-neutral-50 p-4 md:flex-row md:items-center md:justify-between"
            >
              <div className="space-y-1">
                <p className="text-sm font-semibold text-neutral-900">{therapist.name}</p>
                <p className="text-xs text-neutral-500">
                  {STATUS_LABELS[therapist.status]}・並び順 {index + 1}
                  {therapist.alias ? `・別名: ${therapist.alias}` : null}
                </p>
                {therapist.headline ? (
                  <p className="text-sm text-neutral-600">{therapist.headline}</p>
                ) : null}
                {therapist.specialties.length ? (
                  <p className="text-xs text-neutral-500">
                    得意: {therapist.specialties.join(', ')}
                  </p>
                ) : null}
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <button
                  type="button"
                  onClick={() => handleMove(index, -1)}
                  disabled={index === 0}
                  className="rounded-md border border-neutral-200 px-3 py-1.5 text-xs font-medium text-neutral-600 transition hover:bg-neutral-100 disabled:cursor-not-allowed disabled:text-neutral-300"
                >
                  ↑
                </button>
                <button
                  type="button"
                  onClick={() => handleMove(index, 1)}
                  disabled={index === therapists.length - 1}
                  className="rounded-md border border-neutral-200 px-3 py-1.5 text-xs font-medium text-neutral-600 transition hover:bg-neutral-100 disabled:cursor-not-allowed disabled:text-neutral-300"
                >
                  ↓
                </button>
                <button
                  type="button"
                  onClick={() => openEditForm(therapist.id)}
                  className="rounded-md border border-neutral-200 px-3 py-1.5 text-xs font-medium text-neutral-700 transition hover:bg-neutral-100 disabled:opacity-60"
                  disabled={isLoadingDetail}
                >
                  編集
                </button>
                <button
                  type="button"
                  onClick={() => handleDelete(therapist.id)}
                  className="rounded-md border border-red-200 px-3 py-1.5 text-xs font-medium text-red-600 transition hover:bg-red-50"
                >
                  削除
                </button>
              </div>
            </div>
          ))
        ) : (
          <div className="rounded-md border border-dashed border-neutral-300 bg-neutral-50 px-4 py-6 text-center text-sm text-neutral-600">
            まだ登録されたセラピストがいません。「新しいセラピストを追加」を押して登録を開始してください。
          </div>
        )}
      </div>

      {formState ? (
        <form className="space-y-4 rounded-lg border border-neutral-200 bg-white p-4" onSubmit={handleSubmit}>
          <div className="flex items-center justify-between">
            <p className="text-sm font-semibold text-neutral-800">
              {formState.mode === 'create' ? 'セラピストを追加' : 'セラピストを編集'}
            </p>
            <button
              type="button"
              onClick={closeForm}
              className="text-xs font-medium text-neutral-500 transition hover:text-neutral-800"
              disabled={isSubmitting}
            >
              閉じる
            </button>
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            <label className="space-y-1">
              <span className="text-xs font-semibold text-neutral-600">名前 *</span>
              <input
                value={formState.values.name}
                onChange={(event) => handleValuesChange('name', event.target.value)}
                className="w-full rounded-md border border-neutral-200 px-3 py-2 text-sm"
                placeholder="例: 三上 ゆり"
                required
              />
            </label>
            <label className="space-y-1">
              <span className="text-xs font-semibold text-neutral-600">ニックネーム</span>
              <input
                value={formState.values.alias}
                onChange={(event) => handleValuesChange('alias', event.target.value)}
                className="w-full rounded-md border border-neutral-200 px-3 py-2 text-sm"
                placeholder="例: ゆりちゃん"
              />
            </label>
          </div>
          <label className="space-y-1">
            <span className="text-xs font-semibold text-neutral-600">紹介文</span>
            <input
              value={formState.values.headline}
              onChange={(event) => handleValuesChange('headline', event.target.value)}
              className="w-full rounded-md border border-neutral-200 px-3 py-2 text-sm"
              placeholder="一言キャッチコピーを入力してください。"
            />
          </label>
          <label className="space-y-1">
            <span className="text-xs font-semibold text-neutral-600">プロフィール詳細</span>
            <textarea
              value={formState.values.biography}
              onChange={(event) => handleValuesChange('biography', event.target.value)}
              className="h-28 w-full rounded-md border border-neutral-200 px-3 py-2 text-sm"
              placeholder="経歴や得意な施術、メッセージなどを記載してください。"
            />
          </label>
          <div className="grid gap-3 md:grid-cols-2">
            <label className="space-y-1">
              <span className="text-xs font-semibold text-neutral-600">
                得意な施術 (カンマ / 改行区切り)
              </span>
              <textarea
                value={formState.values.specialties}
                onChange={(event) => handleValuesChange('specialties', event.target.value)}
                className="h-24 w-full rounded-md border border-neutral-200 px-3 py-2 text-sm"
                placeholder="例: ディープリンパ, ヘッドスパ"
              />
            </label>
            <label className="space-y-1">
              <span className="text-xs font-semibold text-neutral-600">
                保有資格 (カンマ / 改行区切り)
              </span>
              <textarea
                value={formState.values.qualifications}
                onChange={(event) => handleValuesChange('qualifications', event.target.value)}
                className="h-24 w-full rounded-md border border-neutral-200 px-3 py-2 text-sm"
                placeholder="例: 日本メンズエステ協会認定, アロマセラピスト"
              />
            </label>
          </div>
          <div
            className={`grid gap-3 ${formState.mode === 'edit' ? 'md:grid-cols-2' : ''}`.trim()}
          >
            <label className="space-y-1">
              <span className="text-xs font-semibold text-neutral-600">経験年数</span>
              <input
                value={formState.values.experienceYears}
                onChange={(event) => handleValuesChange('experienceYears', event.target.value)}
                className="w-full rounded-md border border-neutral-200 px-3 py-2 text-sm"
                type="number"
                min={0}
                placeholder="例: 3"
              />
            </label>
            {formState.mode === 'edit' ? (
              <label className="space-y-1">
                <span className="text-xs font-semibold text-neutral-600">掲載ステータス</span>
                <select
                  value={formState.values.status}
                  onChange={(event) =>
                    handleValuesChange('status', event.target.value as DashboardTherapistSummary['status'])
                  }
                  className="w-full rounded-md border border-neutral-200 px-3 py-2 text-sm"
                >
                  {statusOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
            ) : null}
          </div>
          <label className="flex items-center gap-2 text-sm text-neutral-700">
            <input
              type="checkbox"
              checked={formState.values.isBookingEnabled}
              onChange={(event) => handleValuesChange('isBookingEnabled', event.target.checked)}
            />
            オンライン予約を受け付ける
          </label>
          <label className="space-y-1">
            <span className="text-xs font-semibold text-neutral-600">
              写真 URL (1 行につき 1 件)
            </span>
            <textarea
              value={formState.values.photoUrls}
              onChange={(event) => handleValuesChange('photoUrls', event.target.value)}
              className="h-28 w-full rounded-md border border-neutral-200 px-3 py-2 text-sm"
              placeholder="https://example.com/image01.jpg&#10;https://example.com/image02.jpg"
            />
          </label>
          <div className="flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={closeForm}
              className="rounded-md border border-neutral-200 px-4 py-2 text-sm font-medium text-neutral-600 transition hover:bg-neutral-100"
              disabled={isSubmitting}
            >
              キャンセル
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="inline-flex items-center rounded-md bg-neutral-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-neutral-700 disabled:opacity-60"
            >
              {formState.mode === 'create' ? '追加する' : '保存する'}
            </button>
          </div>
        </form>
      ) : null}
    </Card>
  )
}
