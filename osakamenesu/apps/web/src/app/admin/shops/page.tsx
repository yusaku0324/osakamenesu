"use client"

import { useEffect, useState } from 'react'
import { useToast, ToastContainer } from '@/components/useToast'

const EMPTY_PHONE = ''

type ShopSummary = {
  id: string
  name: string
  area: string
  status: string
  service_type: string
}

type MenuItem = {
  id?: string
  name: string
  price: number
  duration_minutes?: number | null
  description?: string | null
  tags?: string[]
  is_reservable_online?: boolean | null
}

type StaffItem = {
  id?: string
  name: string
  alias?: string | null
  headline?: string | null
  specialties?: string[]
}

type AvailabilitySlot = {
  start_at: string
  end_at: string
  status: 'open' | 'tentative' | 'blocked'
}

type AvailabilityDay = {
  date: string
  slots: AvailabilitySlot[]
}

type ContactInfo = {
  phone?: string
  line_id?: string
  website_url?: string
  reservation_form_url?: string
}

type ShopDetail = {
  id: string
  slug?: string | null
  name: string
  area: string
  price_min: number
  price_max: number
  service_type: string
  service_tags: string[]
  contact: ContactInfo | null
  description?: string | null
  catch_copy?: string | null
  address?: string | null
  photos: string[]
  menus: MenuItem[]
  staff: StaffItem[]
  availability: AvailabilityDay[]
}

function toLocalIso(value?: string | null) {
  if (!value) return ''
  try {
    const date = new Date(value)
    if (Number.isNaN(date.getTime())) return value
    const offset = date.getTimezoneOffset() * 60000
    return new Date(date.getTime() - offset).toISOString().slice(0, 16)
  } catch {
    return value
  }
}

function fromLocalIso(value: string) {
  if (!value) return value
  try {
    const date = new Date(value)
    return date.toISOString()
  } catch {
    return value
  }
}

function emptyMenu(): MenuItem {
  return { name: '', price: 0, duration_minutes: undefined, description: '', tags: [] }
}

function emptyStaff(): StaffItem {
  return { name: '', alias: '', headline: '', specialties: [] }
}

function emptySlot(): AvailabilitySlot {
  const now = new Date()
  const plusHour = new Date(now.getTime() + 60 * 60 * 1000)
  return {
    start_at: toLocalIso(now.toISOString()),
    end_at: toLocalIso(plusHour.toISOString()),
    status: 'open',
  }
}

export default function AdminShopsPage() {
  const [shops, setShops] = useState<ShopSummary[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [detail, setDetail] = useState<ShopDetail | null>(null)
  const [menus, setMenus] = useState<MenuItem[]>([])
  const [staff, setStaff] = useState<StaffItem[]>([])
  const [serviceTags, setServiceTags] = useState<string[]>([])
  const [tagDraft, setTagDraft] = useState<string>('')
  const [contact, setContact] = useState<ContactInfo>({})
  const [availability, setAvailability] = useState<AvailabilityDay[]>([])
  const [description, setDescription] = useState<string>('')
  const [catchCopy, setCatchCopy] = useState<string>('')
  const [address, setAddress] = useState<string>('')
  const [photoUrls, setPhotoUrls] = useState<string[]>([''])
  const { toasts, push, remove } = useToast()
  const [loadingDetail, setLoadingDetail] = useState<boolean>(false)

  useEffect(() => {
    async function loadShops() {
      try {
        const resp = await fetch('/api/admin/shops', { cache: 'no-store' })
        if (!resp.ok) throw new Error('failed to load shops')
        const json = await resp.json()
        setShops(json.items || [])
        if (json.items && json.items.length > 0) {
          setSelectedId(json.items[0].id)
        }
      } catch (err) {
        console.error(err)
        push('error', '店舗一覧の取得に失敗しました')
      }
    }
    loadShops()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    async function loadDetail(id: string) {
      setLoadingDetail(true)
      try {
        const resp = await fetch(`/api/admin/shops/${id}`, { cache: 'no-store' })
        if (!resp.ok) throw new Error('failed to load detail')
        const json = await resp.json()
        setDetail(json)
        setMenus((json.menus || []).map((m: MenuItem) => ({
          ...m,
          tags: (m.tags || []),
        })))
        setStaff((json.staff || []).map((s: StaffItem) => ({
          ...s,
          specialties: (s.specialties || []),
        })))
        setServiceTags(json.service_tags || [])
        setContact({
          phone: json.contact?.phone || EMPTY_PHONE,
          line_id: json.contact?.line_id || '',
          website_url: json.contact?.website_url || '',
          reservation_form_url: json.contact?.reservation_form_url || '',
        })
        setAvailability((json.availability || []).map((day: AvailabilityDay) => ({
          date: day.date,
          slots: (day.slots || []).map(slot => ({
            start_at: toLocalIso(slot.start_at),
            end_at: toLocalIso(slot.end_at),
            status: slot.status,
          })),
        })))
        setDescription(json.description || '')
        setCatchCopy(json.catch_copy || '')
        setAddress(json.address || '')
        const photos: string[] = json.photos && json.photos.length > 0 ? json.photos : ['']
        setPhotoUrls(photos)
      } catch (err) {
        console.error(err)
        push('error', '店舗詳細の取得に失敗しました')
      } finally {
        setLoadingDetail(false)
      }
    }
    if (selectedId) {
      loadDetail(selectedId)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedId])

  function updateMenu(index: number, key: keyof MenuItem, value: any) {
    setMenus(prev => {
      const next = [...prev]
      next[index] = { ...next[index], [key]: value }
      return next
    })
  }

  function updateStaff(index: number, key: keyof StaffItem, value: any) {
    setStaff(prev => {
      const next = [...prev]
      next[index] = { ...next[index], [key]: value }
      return next
    })
  }

  function addServiceTag() {
    const value = tagDraft.trim()
    if (!value) return
    if (serviceTags.includes(value)) {
      setTagDraft('')
      return
    }
    setServiceTags(prev => [...prev, value])
    setTagDraft('')
  }

  function removeServiceTag(index: number) {
    setServiceTags(prev => prev.filter((_, idx) => idx !== index))
  }

  function updatePhotoUrl(index: number, value: string) {
    setPhotoUrls(prev => {
      const next = [...prev]
      next[index] = value
      return next
    })
  }

  function addPhotoField() {
    setPhotoUrls(prev => [...prev, ''])
  }

  function removePhotoField(index: number) {
    setPhotoUrls(prev => prev.filter((_, idx) => idx !== index))
  }

  function updateSlot(dayIndex: number, slotIndex: number, key: keyof AvailabilitySlot, value: any) {
    setAvailability(prev => {
      const next = [...prev]
      const day = { ...next[dayIndex] }
      const slots = [...day.slots]
      slots[slotIndex] = { ...slots[slotIndex], [key]: value }
      day.slots = slots
      next[dayIndex] = day
      return next
    })
  }

  function addSlot(dayIndex: number) {
    setAvailability(prev => {
      const next = [...prev]
      const day = { ...next[dayIndex] }
      day.slots = [...day.slots, emptySlot()]
      next[dayIndex] = day
      return next
    })
  }

  function removeSlot(dayIndex: number, slotIndex: number) {
    setAvailability(prev => {
      const next = [...prev]
      const day = { ...next[dayIndex] }
      day.slots = day.slots.filter((_, idx) => idx !== slotIndex)
      next[dayIndex] = day
      return next
    })
  }

  function addAvailabilityDay() {
    setAvailability(prev => [...prev, { date: '', slots: [emptySlot()] }])
  }

  function updateAvailabilityDate(index: number, value: string) {
    setAvailability(prev => {
      const next = [...prev]
      next[index] = { ...next[index], date: value }
      return next
    })
  }

  async function saveContent() {
    if (!selectedId) return
    try {
      const payload = {
        service_tags: serviceTags,
        menus: menus.map(menu => ({
          ...menu,
          price: Number(menu.price) || 0,
          duration_minutes: menu.duration_minutes ? Number(menu.duration_minutes) : undefined,
          tags: (menu.tags || []).filter(Boolean),
        })),
        staff: staff.map(member => ({
          ...member,
          specialties: (member.specialties || []).filter(Boolean),
        })),
        contact: {
          phone: contact.phone || undefined,
          line_id: contact.line_id || undefined,
          website_url: contact.website_url || undefined,
          reservation_form_url: contact.reservation_form_url || undefined,
        },
        description: description || undefined,
        catch_copy: catchCopy || undefined,
        address: address || undefined,
        photos: photoUrls.map(url => url.trim()).filter(Boolean),
      }
      const resp = await fetch(`/api/admin/shops/${selectedId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (!resp.ok) {
        const detailResp = await resp.json().catch(() => ({}))
        push('error', detailResp?.detail || '保存に失敗しました')
        return
      }
      const json = await resp.json()
      setDetail(json)
      setPhotoUrls(json.photos && json.photos.length > 0 ? json.photos : [''])
      push('success', '店舗情報を保存しました')
    } catch (err) {
      console.error(err)
      push('error', 'ネットワークエラーが発生しました')
    }
  }

  async function saveAvailability(date: string, slots: AvailabilitySlot[]) {
    if (!selectedId) return
    if (!date) {
      push('error', '日付を入力してください')
      return
    }
    try {
      const payload = {
        date,
        slots: slots.map(slot => ({
          start_at: fromLocalIso(slot.start_at),
          end_at: fromLocalIso(slot.end_at),
          status: slot.status,
        })),
      }
      const resp = await fetch(`/api/admin/shops/${selectedId}/availability`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (!resp.ok) {
        const detailResp = await resp.json().catch(() => ({}))
        push('error', detailResp?.detail || '空き枠の保存に失敗しました')
        return
      }
      push('success', `${date} の空き枠を保存しました`)
    } catch (err) {
      console.error(err)
      push('error', 'ネットワークエラーが発生しました')
    }
  }

  if (!detail || !selectedId) {
    return (
      <main className="max-w-5xl mx-auto p-4 space-y-4">
        <h1 className="text-2xl font-semibold">店舗管理</h1>
        <p className="text-sm text-slate-500">店舗を選択してください。</p>
        <ToastContainer toasts={toasts} onDismiss={remove} />
      </main>
    )
  }

  return (
    <main className="max-w-6xl mx-auto p-4 space-y-6">
      <div className="flex flex-wrap items-start gap-4">
        <aside className="w-full md:w-64 border rounded-lg bg-white shadow-sm">
          <div className="border-b px-3 py-2 text-sm font-semibold">店舗一覧</div>
          <ul className="max-h-[60vh] overflow-y-auto">
            {shops.map(shop => (
              <li key={shop.id}>
                <button
                  onClick={() => setSelectedId(shop.id)}
                  className={`w-full text-left px-3 py-2 text-sm hover:bg-slate-100 ${shop.id === selectedId ? 'bg-blue-50 font-semibold' : ''}`}
                >
                  <div>{shop.name}</div>
                  <div className="text-xs text-slate-500">{shop.area} / {shop.status}</div>
                </button>
              </li>
            ))}
          </ul>
        </aside>

        <section className="flex-1 space-y-6">
          <header className="space-y-1">
            <h1 className="text-2xl font-semibold">{detail.name}</h1>
            <p className="text-sm text-slate-600">{detail.area} / {detail.service_type} / ¥{detail.price_min.toLocaleString()}〜¥{detail.price_max.toLocaleString()}</p>
            {loadingDetail ? <p className="text-xs text-slate-400">読み込み中...</p> : null}
          </header>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">店舗紹介文</label>
              <textarea
                value={description}
                onChange={e => setDescription(e.target.value)}
                rows={4}
                className="w-full border rounded px-3 py-2 text-sm"
                data-testid="shop-description"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">キャッチコピー</label>
              <textarea
                value={catchCopy}
                onChange={e => setCatchCopy(e.target.value)}
                rows={4}
                className="w-full border rounded px-3 py-2 text-sm"
                data-testid="shop-catch-copy"
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">住所</label>
            <input
              value={address}
              onChange={e => setAddress(e.target.value)}
              className="w-full border rounded px-3 py-2 text-sm"
              data-testid="shop-address"
            />
          </div>

          <section className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-slate-700">掲載写真URL</label>
              <button onClick={addPhotoField} className="border px-3 py-1 rounded text-sm" type="button">行を追加</button>
            </div>
            <div className="space-y-2">
              {photoUrls.map((url, idx) => (
                <div key={`photo-${idx}`} className="flex flex-col gap-2 sm:flex-row sm:items-center">
                  <input
                    value={url}
                    onChange={e => updatePhotoUrl(idx, e.target.value)}
                    className="flex-1 border rounded px-3 py-2 text-sm font-mono"
                    placeholder="https://example.com/photo.jpg"
                    data-testid="shop-photo-input"
                  />
                  <div className="flex gap-2">
                    <button onClick={() => removePhotoField(idx)} className="text-xs text-red-600" type="button" disabled={photoUrls.length <= 1}>削除</button>
                  </div>
                </div>
              ))}
            </div>
            <p className="text-xs text-slate-500">公開ページに表示する画像のURLを1行ずつ入力してください。</p>
          </section>

          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">サービスタグ</label>
            <div className="flex flex-wrap gap-2" data-testid="shop-service-tags">
              {serviceTags.length === 0 ? (
                <span className="text-xs text-slate-400 border border-dashed rounded px-2 py-1">タグ未設定</span>
              ) : (
                serviceTags.map((tag, idx) => (
                  <span key={`${tag}-${idx}`} className="inline-flex items-center gap-1 bg-blue-50 text-blue-700 text-xs px-2 py-1 rounded-full">
                    {tag}
                    <button onClick={() => removeServiceTag(idx)} className="hover:text-blue-900" type="button" aria-label={`${tag} を削除`}>
                      ×
                    </button>
                  </span>
                ))
              )}
            </div>
            <div className="flex gap-2">
              <input
                value={tagDraft}
                onChange={e => setTagDraft(e.target.value)}
                onKeyDown={e => {
                  if (e.key === 'Enter') {
                    e.preventDefault()
                    addServiceTag()
                  }
                }}
                className="flex-1 border rounded px-3 py-2 text-sm"
                placeholder="例: 指圧, アロマ"
              />
              <button onClick={addServiceTag} className="border px-3 py-1 rounded text-sm" type="button">追加</button>
            </div>
          </div>

          <section className="space-y-3">
            <h2 className="text-lg font-semibold">連絡先</h2>
            <div className="grid gap-2 md:grid-cols-2">
              <input
                value={contact.phone || ''}
                onChange={e => setContact(prev => ({ ...prev, phone: e.target.value }))}
                className="border rounded px-3 py-2 text-sm"
                placeholder="電話番号"
              />
              <input
                value={contact.line_id || ''}
                onChange={e => setContact(prev => ({ ...prev, line_id: e.target.value }))}
                className="border rounded px-3 py-2 text-sm"
                placeholder="LINE ID / URL"
              />
              <input
                value={contact.website_url || ''}
                onChange={e => setContact(prev => ({ ...prev, website_url: e.target.value }))}
                className="border rounded px-3 py-2 text-sm"
                placeholder="公式サイトURL"
              />
              <input
                value={contact.reservation_form_url || ''}
                onChange={e => setContact(prev => ({ ...prev, reservation_form_url: e.target.value }))}
                className="border rounded px-3 py-2 text-sm"
                placeholder="WEB予約フォームURL"
              />
            </div>
          </section>

          <section className="space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">メニュー</h2>
              <button onClick={() => setMenus(prev => [...prev, emptyMenu()])} className="border px-3 py-1 rounded text-sm">メニューを追加</button>
            </div>
            <div className="space-y-3">
              {menus.map((menu, idx) => (
                <div
                  key={menu.id || idx}
                  className="border rounded-lg bg-white shadow-sm p-3 space-y-2"
                  data-testid="menu-item"
                >
                  <div className="grid gap-2 md:grid-cols-[2fr_1fr_1fr]">
                    <input
                      value={menu.name}
                      onChange={e => updateMenu(idx, 'name', e.target.value)}
                      className="border rounded px-3 py-2 text-sm"
                      placeholder="メニュー名"
                    />
                    <input
                      value={menu.price}
                      onChange={e => updateMenu(idx, 'price', Number(e.target.value))}
                      className="border rounded px-3 py-2 text-sm"
                      type="number"
                      min={0}
                      placeholder="価格"
                    />
                    <input
                      value={menu.duration_minutes ?? ''}
                      onChange={e => updateMenu(idx, 'duration_minutes', e.target.value ? Number(e.target.value) : undefined)}
                      className="border rounded px-3 py-2 text-sm"
                      type="number"
                      min={0}
                      placeholder="時間(分)"
                    />
                  </div>
                  <textarea
                    value={menu.description || ''}
                    onChange={e => updateMenu(idx, 'description', e.target.value)}
                    className="w-full border rounded px-3 py-2 text-sm"
                    rows={2}
                    placeholder="説明"
                  />
                  <input
                    value={(menu.tags || []).join(', ')}
                    onChange={e => updateMenu(idx, 'tags', e.target.value.split(',').map(tag => tag.trim()).filter(Boolean))}
                    className="border rounded px-3 py-2 text-sm w-full"
                    placeholder="タグ (カンマ区切り)"
                  />
                  <div className="flex justify-end">
                    <button onClick={() => setMenus(prev => prev.filter((_, i) => i !== idx))} className="text-xs text-red-600">削除</button>
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className="space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">スタッフ</h2>
              <button onClick={() => setStaff(prev => [...prev, emptyStaff()])} className="border px-3 py-1 rounded text-sm">スタッフを追加</button>
            </div>
            <div className="space-y-3">
              {staff.map((member, idx) => (
                <div
                  key={member.id || idx}
                  className="border rounded-lg bg-white shadow-sm p-3 space-y-2"
                  data-testid="staff-item"
                >
                  <div className="grid gap-2 md:grid-cols-2">
                    <input
                      value={member.name}
                      onChange={e => updateStaff(idx, 'name', e.target.value)}
                      className="border rounded px-3 py-2 text-sm"
                      placeholder="名前"
                    />
                    <input
                      value={member.alias || ''}
                      onChange={e => updateStaff(idx, 'alias', e.target.value)}
                      className="border rounded px-3 py-2 text-sm"
                      placeholder="表示名"
                    />
                  </div>
                  <textarea
                    value={member.headline || ''}
                    onChange={e => updateStaff(idx, 'headline', e.target.value)}
                    className="w-full border rounded px-3 py-2 text-sm"
                    rows={2}
                    placeholder="紹介文"
                  />
                  <input
                    value={(member.specialties || []).join(', ')}
                    onChange={e => updateStaff(idx, 'specialties', e.target.value.split(',').map(tag => tag.trim()).filter(Boolean))}
                    className="border rounded px-3 py-2 text-sm w-full"
                    placeholder="得意分野 (カンマ区切り)"
                  />
                  <div className="flex justify-end">
                    <button onClick={() => setStaff(prev => prev.filter((_, i) => i !== idx))} className="text-xs text-red-600">削除</button>
                  </div>
                </div>
              ))}
            </div>
          </section>

          <button onClick={saveContent} className="px-4 py-2 rounded bg-blue-600 text-white shadow disabled:opacity-50" disabled={loadingDetail}>
            店舗情報を保存
          </button>

          <section className="space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">空き枠</h2>
              <button onClick={addAvailabilityDay} className="border px-3 py-1 rounded text-sm">日付を追加</button>
            </div>
            <div className="space-y-4">
              {availability.map((day, dayIndex) => (
                <div
                  key={`${day.date}-${dayIndex}`}
                  className="border rounded-lg bg-white shadow-sm p-3 space-y-3"
                  data-testid="availability-day"
                >
                  <div className="flex items-center gap-2">
                    <input
                      type="date"
                      value={day.date}
                      onChange={e => updateAvailabilityDate(dayIndex, e.target.value)}
                      className="border rounded px-3 py-2 text-sm"
                      data-testid="availability-date"
                    />
                    <button onClick={() => setAvailability(prev => prev.filter((_, idx) => idx !== dayIndex))} className="text-xs text-red-600">削除</button>
                  </div>
                  <div className="space-y-2">
                    {day.slots.map((slot, slotIndex) => (
                      <div
                        key={slotIndex}
                        className="grid gap-2 md:grid-cols-[1fr_1fr_1fr_auto] items-center"
                        data-testid="availability-slot"
                      >
                        <input
                          type="datetime-local"
                          value={slot.start_at}
                          onChange={e => updateSlot(dayIndex, slotIndex, 'start_at', e.target.value)}
                          className="border rounded px-3 py-2 text-sm"
                          data-testid="slot-start"
                        />
                        <input
                          type="datetime-local"
                          value={slot.end_at}
                          onChange={e => updateSlot(dayIndex, slotIndex, 'end_at', e.target.value)}
                          className="border rounded px-3 py-2 text-sm"
                          data-testid="slot-end"
                        />
                        <select
                          value={slot.status}
                          onChange={e => updateSlot(dayIndex, slotIndex, 'status', e.target.value)}
                          className="border rounded px-3 py-2 text-sm"
                          data-testid="slot-status"
                        >
                          <option value="open">open</option>
                          <option value="tentative">tentative</option>
                          <option value="blocked">blocked</option>
                        </select>
                        <button onClick={() => removeSlot(dayIndex, slotIndex)} className="text-xs text-red-600">削除</button>
                      </div>
                    ))}
                    <button onClick={() => addSlot(dayIndex)} className="text-xs text-blue-600" data-testid="add-slot">枠を追加</button>
                  </div>
                  <div className="flex justify-end">
                    <button
                      onClick={() => saveAvailability(day.date, day.slots)}
                      className="px-3 py-1 rounded bg-emerald-600 text-white text-sm"
                      data-testid="save-availability"
                    >
                      この日の空き枠を保存
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </section>
      </div>

      <ToastContainer toasts={toasts} onDismiss={remove} />
    </main>
  )
}
