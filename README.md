# Osaka × メンズエステ — 開発環境

ローカルで MVP を最速で検証できるよう、Web(Next.js) + API(FastAPI) + Postgres + Meilisearch を docker-compose で起動できる構成を用意しました。

## セットアップ

```
cd osaka-menesu
cp -n .env.example .env
make dev   # db/meili/api/web が立ち上がります
```

アクセス:
- Web: http://localhost:3000
- API: http://localhost:8000/healthz → `{ "ok": true }`
- Meilisearch: http://localhost:7700 (APIキーは `.env` の `MEILI_MASTER_KEY`)
- Postgres: `localhost:5432` (user/pass/db は `.env`)

## ディレクトリ

```
osaka-menesu/
  apps/web         # Next.js(App Router) — フロント
  services/api     # FastAPI — API
  docker-compose.yml
  .env.example
  Makefile
```

## 次の実装ガイド

- 検索: API `/api/profiles/search` を Meilisearch に接続し、facet(エリア/料金/タグ)と sort を実装
- 詳細: `/profiles/:id` で料金/出勤/日記3件/CTA を表示
- /out/:token: ローカルは FastAPI の 302、運用は Cloudflare Workers+KV へ置き換え
- 画像: S3互換(例: MinIO) → Cloudflare CDN、`next/image` で AVIF/WebP + LQIP
- 18+ゲート/SEO/構造化データ: Next Middleware + JSON-LD を追加

## よく使うコマンド

```
make up        # db/meili を先に起動
make api       # API を起動(ホットリロード)
make web       # Web を起動(ホットリロード)
make logs      # 全ログ
make down      # 停止
```

## メモ

- 本番は API/DB/検索を別プロセス & CDN キャッシュ/ISR を併用
- クリック計測は Cloudflare Workers へ移行し、ダッシュボードは日/週集計
- スキーマ/ER は 要件ドキュメント の通り。Alembic を追加してマイグレーションを管理予定

## データ投入フロー（WIP）

`tools/import_shops_from_yaml.py` で YAML から店舗データを流し込めます。サンプルは `data/sample_shops.yaml`。

```
cd osaka-menesu
python tools/import_shops_from_yaml.py data/sample_shops.yaml --api-base http://localhost:8000 --admin-key dev_admin_key
```

YAMLには以下の情報を記載できます:
- `name`, `area`, `price_min`, `price_max`, `service_type`
- `photos` (配列), `tags`(=service_tags), `discounts`, `badges`
- `contact.phone/line/website/reservation_form_url/sns`
- `menus` (name/price/duration_minutes/tags/description)
- `staff` (name/alias/headline/specialties)
- `availability.{YYYY-MM-DD}` の配列（`start_at`, `end_at`, `status`）

スクリプトは以下を実行します:
1. `/api/admin/profiles` で店舗作成（`contact_json` に menus/staff を格納）
2. `/api/admin/availabilities/bulk` で出勤データ投入
3. 任意の LINE/TEL/WEB を `/api/admin/outlinks` へ作成
4. `/api/admin/reindex` で Meilisearch を同期

※ `services/api/requirements.txt` に `PyYAML` を追加したので、`pip install -r requirements.txt` の再実行が必要です。
