import Link from 'next/link'

export default function Page() {
  return (
    <main className="max-w-5xl mx-auto p-4 space-y-6">
      <header className="flex items-center">
        <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-slate-900 to-slate-600">大阪メンエス.com</h1>
      </header>

      <section className="grid gap-3 md:grid-cols-4">
        <select className="border rounded p-2">
          <option>難波/日本橋</option>
          <option>梅田</option>
          <option>心斎橋</option>
          <option>天王寺</option>
          <option>谷町九丁目</option>
          <option>堺筋本町</option>
          <option>京橋</option>
          <option>北新地</option>
          <option>本町</option>
          <option>南森町</option>
          <option>新大阪</option>
          <option>江坂</option>
          <option>堺</option>
        </select>
        <div className="flex gap-2">
          <select className="border rounded p-2">
            <option>最低(万)</option>
            <option>1万</option>
            <option>2万</option>
            <option>3万</option>
            <option>4万</option>
            <option>5万</option>
            <option>6万</option>
            <option>7万</option>
            <option>8万</option>
            <option>9万</option>
            <option>10万</option>
          </select>
          <select className="border rounded p-2">
            <option>最高(万)</option>
            <option>1万</option>
            <option>2万</option>
            <option>3万</option>
            <option>4万</option>
            <option>5万</option>
            <option>6万</option>
            <option>7万</option>
            <option>8万</option>
            <option>9万</option>
            <option>10万</option>
          </select>
        </div>
        <select className="border rounded p-2"><option>バスト: C</option><option>D</option><option>E</option><option>F</option><option>G</option><option>H</option><option>I</option><option>J</option><option>K以上</option></select>
        <label className="inline-flex items-center gap-2"><input type="checkbox" /> 本日出勤</label>
      </section>

      <div>
        <Link href="/search" className="inline-block bg-blue-600 text-white rounded px-4 py-2">検索する</Link>
      </div>
    </main>
  )
}
