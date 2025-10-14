export type SampleStaff = {
  id: string
  name: string
  alias?: string | null
  headline?: string | null
  rating?: number | null
  review_count?: number | null
  avatar_url?: string | null
  specialties?: string[] | null
}

export type SampleAvailabilitySlot = {
  start_at: string
  end_at: string
  status: 'open' | 'tentative' | 'blocked'
  staff_id?: string | null
  menu_id?: string | null
}

export type SampleAvailabilityDay = {
  date: string
  is_today?: boolean | null
  slots: SampleAvailabilitySlot[]
}

export type SampleContact = {
  phone?: string | null
  line_id?: string | null
  website_url?: string | null
  reservation_form_url?: string | null
  sns?: Array<{ platform: string; url: string; label?: string | null }> | null
}

export type SampleShop = {
  id: string
  slug?: string | null
  name: string
  store_name?: string | null
  area: string
  area_name?: string | null
  min_price: number
  max_price: number
  description?: string | null
  catch_copy?: string | null
  photos?: Array<{ url: string }> | null
  contact?: SampleContact | null
  menus?: Array<{
    id: string
    name: string
    description?: string | null
    duration_minutes?: number | null
    price: number
    tags?: string[] | null
  }> | null
  staff?: SampleStaff[] | null
  availability_calendar?: {
    shop_id: string
    generated_at: string
    days: SampleAvailabilityDay[]
  } | null
  badges?: string[] | null
  today_available?: boolean | null
  service_tags?: string[] | null
  metadata?: Record<string, unknown> | null
  promotions?: Array<{ label: string; description?: string | null; expires_at?: string | null }> | null
  ranking_reason?: string | null
  reviews?: {
    average_score?: number | null
    review_count?: number | null
    highlighted?: Array<{
      review_id?: string | null
      title: string
      body: string
      score: number
      visited_at?: string | null
      author_alias?: string | null
    }> | null
  } | null
  diary_count?: number | null
  has_diaries?: boolean | null
  diaries?: Array<{
    id?: string | null
    title?: string | null
    body: string
    photos?: string[] | null
    hashtags?: string[] | null
    published_at?: string | null
  }> | null
}

export const SAMPLE_SHOPS: SampleShop[] = [
  {
    id: 'sample-namba-resort',
    slug: 'sample-namba-resort',
    name: 'アロマリゾート 難波本店',
    store_name: 'アロマリゾート 難波本店',
    area: '難波/日本橋',
    area_name: '難波/日本橋',
    min_price: 11000,
    max_price: 18000,
    description: 'リゾートのような完全個室空間で、丁寧なリンパケアが人気のメンエス。21時以降のビジネス利用も多数。',
    catch_copy: 'リゾートホテルを思わせる完全個室で極上の癒し体験を。',
    photos: [
      { url: 'https://images.unsplash.com/photo-1515378791036-0648a3ef77b2?auto=format&fit=crop&w=1200&q=80' },
      { url: 'https://images.unsplash.com/photo-1523419409543-0c1df022bdd7?auto=format&fit=crop&w=1200&q=80' },
    ],
    contact: {
      phone: '066-100-1234',
      line_id: '@namba-resort',
      website_url: 'https://namba-resort.example.com',
      reservation_form_url: 'https://namba-resort.example.com/reserve',
      sns: [
        { platform: 'Instagram', url: 'https://instagram.com/namba.resort', label: 'Instagram' },
      ],
    },
    menus: [
      {
        id: 'sample-namba-course-90',
        name: 'スタンダードコース 90分',
        description: '全身リンパケア＋ドライヘッドスパ付き。',
        duration_minutes: 90,
        price: 13000,
        tags: ['リンパ', 'ドライヘッド'],
      },
      {
        id: 'sample-namba-course-120',
        name: 'プレミアムコース 120分',
        description: 'ホットストーンとハンドトリートメントで全身をケア。',
        duration_minutes: 120,
        price: 18000,
        tags: ['ホットストーン', 'ハンドケア'],
      },
    ],
    staff: [
      {
        id: 'therapist-aki',
        name: '葵',
        alias: 'Aoi',
        headline: '丁寧なオイルトリートメントで人気のセラピスト',
        rating: 4.6,
        review_count: 87,
        avatar_url: 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=640&q=80',
        specialties: ['リンパ', 'ホットストーン', '指名多数'],
      },
      {
        id: 'therapist-rin',
        name: '凛',
        alias: 'Rin',
        headline: 'ストレッチと指圧を組み合わせた独自施術が評判',
        rating: 4.3,
        review_count: 52,
        avatar_url: 'https://images.unsplash.com/photo-1524504388940-b1c1722653e1?auto=format&fit=crop&w=640&q=80',
        specialties: ['ストレッチ', '指圧', 'ディープリンパ'],
      },
    ],
    availability_calendar: {
      shop_id: 'sample-namba-resort',
      generated_at: '2025-10-07T08:00:00+09:00',
      days: [
        {
          date: '2025-10-07',
          is_today: true,
          slots: [
            {
              start_at: '2025-10-07T21:00:00+09:00',
              end_at: '2025-10-07T23:00:00+09:00',
              status: 'open',
              staff_id: 'therapist-aki',
            },
            {
              start_at: '2025-10-07T19:00:00+09:00',
              end_at: '2025-10-07T21:00:00+09:00',
              status: 'tentative',
              staff_id: 'therapist-rin',
            },
          ],
        },
        {
          date: '2025-10-08',
          slots: [
            {
              start_at: '2025-10-08T18:00:00+09:00',
              end_at: '2025-10-08T20:00:00+09:00',
              status: 'open',
              staff_id: 'therapist-rin',
            },
          ],
        },
      ],
    },
    badges: ['人気店', '駅チカ'],
    today_available: true,
    service_tags: ['個室', '日本人セラピスト', 'ペアルーム対応'],
    promotions: [
      { label: '新人割 ¥1,000OFF', expires_at: '2025-12-31' },
    ],
    ranking_reason: '口コミ評価4.7★。アロマ×リンパケアで全身リフレッシュ。',
    reviews: {
      average_score: 4.7,
      review_count: 128,
      highlighted: [
        {
          review_id: 'rev-1',
          title: '癒やされました',
          body: 'ゆっくりとした接客でリラックスできました。',
          score: 5,
          visited_at: '2025-09-20',
          author_alias: '会社員A',
        },
      ],
    },
    diary_count: 12,
    has_diaries: true,
    diaries: [
      {
        id: 'diary-aki-1',
        title: '本日の空き枠',
        body: '本日は21時〜と23時〜で空きがございます。お仕事帰りにぜひお立ち寄りください。',
        photos: ['https://images.unsplash.com/photo-1523419409543-0c1df022bdd7?auto=format&fit=crop&w=900&q=80'],
        hashtags: ['葵', '当日予約'],
        published_at: '2025-10-01T09:00:00+09:00',
      },
    ],
  },
]
