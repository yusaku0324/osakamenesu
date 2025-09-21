import Image from 'next/image'
import Link from 'next/link'

import { Badge } from '@/components/ui/Badge'
import { Card } from '@/components/ui/Card'
import { Chip } from '@/components/ui/Chip'

export type Promotion = {
  label: string
  description?: string | null
  expires_at?: string | null
  highlight?: string | null
}

export type ShopHit = {
  id: string
  slug?: string | null
  name: string
  store_name?: string | null
  area: string
  area_name?: string | null
  address?: string | null
  categories?: string[] | null
  service_tags?: string[] | null
  min_price: number
  max_price: number
  rating?: number | null
  review_count?: number | null
  lead_image_url?: string | null
  badges?: string[] | null
  today_available?: boolean | null
  next_available_at?: string | null
  distance_km?: number | null
  online_reservation?: boolean | null
  updated_at?: string | null
  promotions?: Promotion[] | null
  ranking_reason?: string | null
}

const formatter = new Intl.NumberFormat('ja-JP')
const dateFormatter = new Intl.DateTimeFormat('ja-JP', { month: 'short', day: 'numeric', weekday: 'short' })

function formatPriceRange(min: number, max: number) {
  if (!min && !max) return '料金情報なし'
  if (min === max) return `¥${formatter.format(min)}`
  return `¥${formatter.format(min)} 〜 ¥${formatter.format(Math.max(min, max))}`
}

function getAvailability(hit: ShopHit): { label: string; tone: 'success' | 'danger' | 'neutral' } | null {
  if (hit.today_available) {
    return { label: '本日予約可能', tone: 'success' }
  }
  if (hit.next_available_at) {
    const at = new Date(hit.next_available_at)
    if (!Number.isNaN(at.getTime())) {
      return { label: `${dateFormatter.format(at)} 受付〇`, tone: 'neutral' }
    }
  }
  return null
}

function getProfileHref(hit: ShopHit) {
  if (hit.slug) return `/profiles/${hit.slug}`
  return `/profiles/${hit.id}`
}

export function ShopCard({ hit }: { hit: ShopHit }) {
  const availability = getAvailability(hit)
  const distanceLabel = (() => {
    if (hit.distance_km == null) return null
    if (hit.distance_km < 0.1) return '駅チカ'
    return `${hit.distance_km.toFixed(1)}km`
  })()

  const updatedLabel = (() => {
    if (!hit.updated_at) return null
    const dt = new Date(hit.updated_at)
    if (Number.isNaN(dt.getTime())) return null
    return `更新 ${dateFormatter.format(dt)}`
  })()

  const primaryPromotion = Array.isArray(hit.promotions)
    ? hit.promotions.find((promo) => promo && promo.label)
    : undefined

  return (
    <Link href={getProfileHref(hit)} className="block focus:outline-none" prefetch>
      <Card interactive className="h-full">
        <div className="relative aspect-[4/3] bg-neutral-surfaceAlt">
          {hit.lead_image_url ? (
            <Image
              src={hit.lead_image_url}
              alt={`${hit.name} の写真`}
              fill
              sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
              className="object-cover"
              priority={false}
            />
          ) : null}

          {Array.isArray(hit.badges) && hit.badges.length ? (
            <div className="absolute left-2 top-2 flex flex-wrap gap-1">
              {hit.badges.slice(0, 2).map((badge) => (
                <Badge key={badge} variant="brand" className="shadow-lg">
                  {badge}
                </Badge>
              ))}
            </div>
          ) : null}
          {distanceLabel ? (
            <div className="absolute right-2 top-2">
              <Badge variant="outline">{distanceLabel}</Badge>
            </div>
          ) : null}
        </div>

          <div className="space-y-3 p-4">
            <div>
              <div className="flex items-start justify-between gap-2">
                <h3 className="text-lg font-semibold tracking-tight text-neutral-text group-hover:text-brand-primary">
                  {hit.name}
                </h3>
                {availability ? (
                  <Badge variant={availability.tone === 'success' ? 'success' : 'neutral'}>{availability.label}</Badge>
                ) : null}
              </div>
              {hit.store_name ? (
                <p className="text-sm text-neutral-textMuted">{hit.store_name}</p>
              ) : null}
              <p className="text-sm text-neutral-textMuted">
                {hit.area_name || hit.area}
                {hit.address ? `｜${hit.address}` : ''}
              </p>
              {hit.ranking_reason ? (
                <p className="mt-1 text-xs text-neutral-textMuted line-clamp-2">{hit.ranking_reason}</p>
              ) : null}
            </div>

            <div className="flex flex-wrap items-center gap-3 text-sm">
              <span className="font-semibold text-brand-primaryDark">{formatPriceRange(hit.min_price, hit.max_price)}</span>
              {hit.rating ? (
              <span className="flex items-center gap-1 text-neutral-text">
                <span aria-hidden className="text-amber-400">★</span>
                <span className="font-semibold">{hit.rating.toFixed(1)}</span>
                {hit.review_count ? <span className="text-xs text-neutral-textMuted">({hit.review_count}件)</span> : null}
              </span>
            ) : null}
            {hit.online_reservation ? <Badge variant="brand">オンライン予約OK</Badge> : null}
            </div>

            {Array.isArray(hit.service_tags) && hit.service_tags.length ? (
              <div className="flex flex-wrap gap-2">
                {hit.service_tags.slice(0, 4).map((tag) => (
                <span
                  key={tag}
                  className="inline-flex items-center rounded-badge border border-neutral-borderLight bg-neutral-surfaceAlt px-2 py-0.5 text-[12px] text-neutral-text"
                >
                  {tag}
                </span>
              ))}
            </div>
          ) : null}

          {primaryPromotion ? (
            <Chip variant="accent" className="text-[11px]">
              {primaryPromotion.label}
            </Chip>
          ) : null}

          {updatedLabel ? (
            <div className="text-xs text-neutral-textMuted">{updatedLabel}</div>
          ) : null}
        </div>
      </Card>
    </Link>
  )
}

export default ShopCard
