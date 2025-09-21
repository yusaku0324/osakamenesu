# 大阪メンエス.com マーケティング情報更新フロー

割引ラベルやランキングバッジを運用に乗せるための手順メモです。更新担当者はこの手順に沿って反映してください。

## 1. 事前準備

- **対象リスト作成**: `profile_id`（UUID）を含むスプレッドシートを用意し、割引・ランキング情報を整理する。
  - 推奨カラム: `profile_id`, `ranking_badges`（カンマ区切り）, `ranking_weight`, `discounts`（JSON 配列）。
  - 例: `[{"label": "新人割", "description": "初回1,000円OFF", "expires_at": "2024-12-31"}]`
- **JSON 化**: スプレッドシートから JSON に変換し、以下のような構造で保存する。

```json
[
  {
    "profile_id": "8664c540-2d76-427f-a12b-8b704fd7e84b",
    "ranking_badges": ["人気No.1", "本日注目"],
    "ranking_weight": 95,
    "discounts": [
      {"label": "新人割", "description": "入店30日以内", "expires_at": "2024-12-31"}
    ]
  }
]
```

## 2. API での反映

1. 管理APIキー（`.env` の `ADMIN_API_KEY`）を確認する。
2. Docker 環境を起動（ローカルの場合）。
3. JSON を使って以下のいずれかで反映する。

### a. ツールスクリプトを使用（推奨）

```bash
cd osaka-menesu/services/api
python tools/apply_marketing.py marketing.json \
  --api-base http://localhost:8000 \
  --admin-key dev_admin_key
```

- `--sleep` オプションでリクエスト間隔を調整できる。
- 成功/失敗が標準出力に表示される。

### b. 単発更新（curl）

```bash
curl -X POST http://localhost:8000/api/admin/profiles/<PROFILE_ID>/marketing \
  -H 'Content-Type: application/json' \
  -H 'X-Admin-Key: dev_admin_key' \
  -d '{
        "ranking_badges": ["人気No.1"],
        "ranking_weight": 90,
        "discounts": [
          {"label": "前日予約割", "description": "前日予約で1,000円OFF"}
        ]
      }'
```

## 3. 反映後の確認

1. `curl -X POST http://localhost:8000/api/admin/reindex -H 'X-Admin-Key: dev_admin_key'` で再インデックス。
2. ブラウザの `/search` / プロフィール詳細ページで表示を確認。
3. 問題があれば JSON を修正して再実行。

## 4. 運用メモ

- ラベルは短く（6〜8文字程度）保つ。
- `ranking_weight` は数値が大きいほど優先表示。未設定は `null` でOK。
- コード変更が発生した場合は `docs/osaka-menesu-design-guide.md` と併せて更新する。

