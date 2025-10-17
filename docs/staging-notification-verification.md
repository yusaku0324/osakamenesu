# ステージング通知ページ 反映フロー

## 1. イメージのビルドとプッシュ

```bash
# ローカルで確認済み
cd /Users/yusaku/Documents/GitHub/osakamenesu
docker compose build osakamenesu-api osakamenesu-web

# GitHub Container Registry (GHCR) へプッシュする例
# 1) write:packages 権限付き PAT を用意してログイン
export GHCR_USER=<your-github-username>
export GHCR_PAT=<personal-access-token>
echo "$GHCR_PAT" | docker login ghcr.io -u "$GHCR_USER" --password-stdin

# 2) タグ付け（ORG は GitHub Org / ユーザー名）
export ORG=yusaku0324
# API イメージ
docker tag osakamenesu-osakamenesu-api ghcr.io/$ORG/osakamenesu-api:staging
# Web イメージ（IMAGE ID は `docker compose images` で確認できる 160ef... 等でも可）
docker tag osakamenesu-osakamenesu-web ghcr.io/$ORG/osakamenesu-web:staging

# 3) プッシュ
docker push ghcr.io/$ORG/osakamenesu-api:staging
docker push ghcr.io/$ORG/osakamenesu-web:staging
```

## 2. ステージング環境の環境変数

| 変数 | 推奨値 | 用途 |
| ---- | ------ | ---- |
| `ADMIN_BASIC_USER` | 管理画面のベーシック認証ユーザー | Playwright・管理画面ログイン |
| `ADMIN_BASIC_PASS` | 管理画面のベーシック認証パスワード | 同上 |
| `ADMIN_API_KEY` | `dev_admin_key` など環境に合わせて | `/api/admin/*` プロキシで利用 |
| `NEXT_PUBLIC_API_BASE` | `/api` or `https://stg-api.example.com` | Web フロントが叩く API URL |
| `API_INTERNAL_BASE` | `http://osakamenesu-api:8000` | docker compose 内部通信 |
| `MEILI_MASTER_KEY` | `dev_meili_master_key` など環境に合わせて | Meilisearch API キー |
| `MEILI_HOST` | `https://stg-meili.example.com` など | API/CI から参照する Meilisearch エンドポイント |
| `CLOUD_RUN_MEILI_SERVICE` | `osakamenesu-meili` など Cloud Run サービス名 | CI から Cloud Run Meilisearch をデプロイする際に使用 |
| `NOTIFY_SMTP_HOST` ほか通知系 | SMTP / Slack / LINE 情報 | 通知送信 |

`.env.staging` の例:

```
ADMIN_BASIC_USER=stg-admin
ADMIN_BASIC_PASS=stg-secret
ADMIN_API_KEY=stg_admin_key
NEXT_PUBLIC_API_BASE=https://stg-api.example.com
API_INTERNAL_BASE=http://osakamenesu-api:8000
NOTIFY_SMTP_HOST=smtp.example.com
NOTIFY_SMTP_PORT=587
NOTIFY_SMTP_USER=no-reply@example.com
NOTIFY_SMTP_PASSWORD=********
NOTIFY_FROM_EMAIL=osakamenesu@example.com
```

## 3. ステージングデータ投入

```bash
python services/api/seed_dev.py \
  --api-base https://stg-api.example.com \
  --admin-key "$ADMIN_API_KEY" \
  --count 6
```

- `profiles` が既に存在する場合は `--count` を減らしても良い。
- 予約テスト用のスクリプトを使う場合は `--api-base` と `--admin-key` を同じ値にする。

## 4. デプロイ手順（docker-compose 例）

```bash
ssh staging-host
cd /opt/osakamenesu
export $(cat .env.staging | xargs)
docker compose pull osakamenesu-api osakamenesu-web
docker compose up -d osakamenesu-api osakamenesu-web
```

## 5. 動作確認チェック

1. `https://stg-web.example.com/dashboard/<profileId>/notifications` が 200 で開ける。
2. メール/LINE/Slack の有効化・保存・テスト送信が成功（レスポンス 200/204）。
3. 別ブラウザで更新 → 楽観ロックのメッセージが出て再保存できる。
4. `/api/dashboard/shops/<id>/notifications` が 200 を返す（Cookie 認証要）。
5. 予約作成フローで通知が実際に配信されるかを確認。
6. `npm run test` を `E2E_BASE_URL` 等ステージング設定で再実行し、管理画面シナリオが PASS すること。

Playwright の例:

```bash
cd apps/web
E2E_BASE_URL=https://stg-web.example.com \
ADMIN_BASIC_USER=stg-admin \
ADMIN_BASIC_PASS=stg-secret \
ADMIN_API_KEY=stg_admin_key \
npm run test
```

## 6. ロールバック

- 旧イメージに戻す場合は `docker compose up -d osakamenesu-web=osakamenesu-web@sha256:<old>` のように digest 指定。
- 通知設定で問題が出た場合は `profiles` テーブルの通知列を旧状態に戻し、再保存する。

## 7. 共有事項

- 作業完了後に Slack #osakamenesu-dev などで「ステージング通知UI反映完了」を報告。
- `docs/backlog.md` 等にもステージング確認済みの記録を残す。
![alt text](image.png)
