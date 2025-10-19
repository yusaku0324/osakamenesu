import Gallery from '@/components/Gallery'

export default function GalleryDemoPage() {
  const photos = [
    'https://picsum.photos/seed/menesu-demo-1/800/600',
    'https://picsum.photos/seed/menesu-demo-2/800/600',
    'https://picsum.photos/seed/menesu-demo-3/800/600',
    'https://picsum.photos/seed/menesu-demo-4/800/600',
    'https://picsum.photos/seed/menesu-demo-5/800/600',
  ]
  return (
    <main className="max-w-3xl mx-auto p-4 space-y-4">
      <header className="flex items-center justify-between">
        <h1 className="text-xl font-bold">Gallery Demo</h1>
        <a href="/" className="text-blue-600">トップへ</a>
      </header>
      <Gallery photos={photos} altBase="Demo" />
      <p className="text-sm text-slate-600">サムネ/ドットのクリック、スワイプ/フリックでの移動、LQIP表示を確認できます。</p>
    </main>
  )
}

