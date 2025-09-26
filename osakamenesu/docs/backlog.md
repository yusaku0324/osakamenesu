# 大阪メンエス.com 機能バックログ（優先度付き）

本書は要件定義で挙げた未対応項目を整理し、優先度と初手タスクをまとめたものです。優先度は P0 (最優先) / P1 / P2 / P3 の 4 段階で定義します。

| ID | 項目 | 優先度 | 背景/期待効果 | 初手タスク | 所感 |
| --- | --- | --- | --- | --- | --- |
| BL-001 | 予約通知連携（メール/SMS/LINE） | **P0** | 予約フォーム送信後に店舗側が即時把握できず、機会損失リスクが高い。 | - 通知チャネル候補を決定（メール + LINE Notify など）<br>- 通知テンプレートと送信先を設定可能にする DB 項目を追加<br>- FastAPI 側で予約作成時に非同期送信処理を実装 | 通知遅延は UX 直結。早期に最小チャネル（メール）だけでも稼働させる。 |
| BL-002 | 店舗セルフ管理 UI（ダッシュボード） | **P0** | 現状は運営が API/key で手動更新しており、店舗回転が上がると運用負荷が破綻する。 | - 店舗アカウント概念と認証方式を決定（メール + Magic Link など）<br>- Next.js 側に `/dashboard` を用意しプロフィール・シフト・日記編集を行えるフォームを設計<br>- 権限チェック付き API エンドポイントを追加 | 大型機能だが今後のスケールに必須。段階的リリースを想定。 |
| BL-003 | エンドユーザ会員ログイン/お気に入り | **P1** | 会員機能が無いため、再訪や予約履歴の管理ができない。顧客ロイヤリティを高めたい。 | - 利用者アカウントモデルを設計（メール or LINE 連携）<br>- お気に入り店舗/閲覧履歴の保存スキーマ策定<br>- フロントで「お気に入り」「閲覧履歴」UI を追加 | 店舗側成果指標を高めるための中期改善。セルフ管理 UI の後着手。 |
| BL-004 | 地図・駅別検索 / 距離ソート | **P1** | エリア粒度が粗く、駅近や現在地周辺検索ができない。競合（シティヘブン等）との差別化に必要。 | - `GeoLocation` を元に Meilisearch で距離ソートできるようスキーマ更新<br>- Map コンポーネント (Mapbox/Google Maps) の導入検証<br>- 駅コード辞書を整備して facet/フィルタに追加 | 位置情報を既に保持しているため実装可能。UI 作り込みに時間を要する。 |
| BL-005 | 広告メニュー管理（PR枠/クーポン管理） | **P2** | 現状プロモーションは手動 JSON 管理。広告課金を見据えた枠管理・レポーティングが無い。 | - PR 枠の種別と表示ロジックを要件化<br>- 課金プラン/露出期間を管理するテーブル追加<br>- 表示ログ計測とダッシュボード案を作成 | 収益化ポイント。セルフ管理 UI と連動させると効果大。 |
| BL-006 | 観測性強化（エラーレポート・トラッキング） | **P2** | GA のみだと API 障害や予約失敗が検知できない。品質リスク。 | - Sentry 等の APM 導入検討<br>- API ログの構造化（JSON logging）<br>- 予約エラー時の告知チャネル整備 | 優先度は中程度だが早めに仕込みたい。通知基盤とセットで進める。 |
| BL-007 | コンテンツ SEO / CMS 連携 | **P3** | 初めての方向け記事やブログを手作業で更新予定。CMS 化で更新効率を上げたい。 | - CMS 選定（Contentful / microCMS / Notion API 等）<br>- `/demo/blog` の静的生成/ISR 設計<br>- 記事コンポーネントのデザイン整備 | 他優先項目の後。MVP 成功後に強化。 |

## 実行メモ

- P0 タスク（BL-001, BL-002）は直近スプリントで着手し、通知→セルフ管理の順に進める想定。
- P1 以降は P0 の進捗を見ながらロードマップ化。位置情報検索はバックエンド改修が比較的軽いため前倒し候補。
- バックログは定期的に見直し、本ドキュメントへ追記する。

## P0 スプリント計画（レビュー結果）

| タスク | 期間 | オーナー | マイルストーン | 補足 |
| --- | --- | --- | --- | --- |
| BL-001 予約通知連携 | Sprint 24-07 (2 週間) | Backend: @taro.dev<br>Infra 支援: @akane.ops | Day 3: 通知チャネル決定と設計レビュー<br>Day 7: メール送信実装 + ステージング動作確認<br>Day 10: LINE Notify/Slack webhook の PoC<br>Day 14: 本番向け設定手順書を更新 | FastAPI で `BackgroundTasks` を利用し非同期送信。秘密情報は `.env` 管理。通知失敗時のリトライ/アラート設計を並走。 |
| BL-002 店舗セルフ管理 UI | Sprint 24-08〜24-09 (4 週間) | Frontend: @yuki.ui<br>Backend: @suzuki.api | Sprint 24-08 Day 5: 認証フロー仕様確定（Magic Link 案）<br>Day 10: `/dashboard` ワイヤー案 & API 下書きレビュー<br>Sprint 24-09 Day 5: プロフィール編集 MVP リリース<br>Day 20: シフト/日記編集とアクセス権限テーブル実装 | 認証には Supabase Auth を暫定採用。初期リリースはプロファイル編集＋通知先設定に絞る。QA 専任をアサインし UAT 実施。 |

- @pm-lead がスプリント開始時にタスク分解（チケット化）とバーンダウンの管理を担当。
- 依存タスク（例: 通知で利用するメール送信サービス契約）はオーナーが別途 Issues/TODO として起票。
- レビューは週次（火曜）スタンドアップで進捗共有し、遅延時は優先度調整を行う。

### BL-002 ダッシュボード通知設定 詳細仕様

Dashboard の初期スコープでは「通知設定」タブを MVP として提供し、店舗オーナー自身が送信チャネルを切り替えられるようにする。以下に UI フローと API 仕様、バリデーション/エラー整理を記載する。

#### 想定ユーザーフロー

1. 店舗担当者が `/dashboard/login` でメールアドレスを入力し、Magic Link でサインイン（Supabase Auth）。
2. 認証後 `/dashboard` へ遷移し、複数店舗を持つアカウントは「店舗選択ダイアログ」で `profile_id` を選択。
3. サイドバーから「通知設定」を選択。`GET /api/dashboard/shops/{profile_id}/notifications` を叩き既存設定を取得。
4. フォームでメール/LINE/Slack の宛先や有効・無効を編集。リアルタイムバリデーションでエラー表示。
5. 「テスト送信」ボタンを押すと `POST /api/dashboard/shops/{profile_id}/notifications/test` を呼び、成功/失敗をトースト表示。
6. 「保存」で `PUT /api/dashboard/shops/{profile_id}/notifications` を実行し、成功時はグリーンのサクセスメッセージと直近保存者/時刻を更新。
7. API が `409`（楽観ロック）を返した場合はダイアログで「他の担当者が更新しました。再読み込みしてから編集してください」と案内。
8. `401/403` 発生時はグローバルエラーバナーを表示し、ログアウト→再ログインを促す。

#### フォーム構成とバリデーション

| UI 要素 | API フィールド | 入力形式 / 制約 | バリデーションメッセージ例 |
| --- | --- | --- | --- |
| 通知メール（最大 5 件） | `emails: string[]` | RFC 準拠メール形式。重複禁止。最大 5 件。 | `有効なメールアドレスを入力してください` / `同じメールアドレスは 1 度だけ設定できます` |
| メール送信 ON/OFF | `channels.email.enabled: bool` | 少なくとも 1 チャネルが ON であること。 | `少なくとも 1 つの通知チャネルを有効化してください` |
| LINE Notify トークン | `channels.line.token: string` | 43 文字の英数字・記号 `[-_+]` のみ。空は無効扱い。 | `LINE Notify トークン形式が不正です` |
| LINE 通知 ON/OFF | `channels.line.enabled: bool` | `enabled=true` の場合トークン必須。 | `LINE 通知を有効化するにはトークンを入力してください` |
| Slack Webhook URL | `channels.slack.webhook_url: string` | `https://hooks.slack.com/` で始まる URL。最大 200 文字。 | `Slack Webhook URL が正しくありません` |
| Slack 通知 ON/OFF | `channels.slack.enabled: bool` | `enabled=true` の場合 URL 必須。 | `Slack 通知を有効化するには Webhook URL を入力してください` |
| 予約状態フィルタ | `trigger_status: string[]` | `pending`, `confirmed`, `declined`, `cancelled`, `expired` の組み合わせ。空は全て。 | `通知対象ステータスを選択してください` |
| テスト送信ボタン | - | 押下中はローディング。API エラーはそのままトースト表示。 | `通知の送信に失敗しました。入力内容を確認してください` |

- 既存 DB への書き込みは `profiles.notify_emails (TEXT[])`, `profiles.notify_line_token (TEXT)`, `profiles.notify_slack_webhook (TEXT)` などの列（別途マイグレーション）を想定。`updated_at` をレスポンスに含めダッシュボードで楽観ロック比較に使用する。
- UI では空配列/空文字を「未設定」とし、保存時に API へ null ではなく空値として送信。
- 全チャネル OFF + 宛先空の場合は `422` を返す方針。

#### API 仕様（案）

```
GET  /api/dashboard/shops/{profile_id}/notifications
200 OK
{
  "profile_id": "uuid",
  "updated_at": "2025-09-25T12:34:56Z",
  "channels": {
    "email": {"enabled": true, "recipients": ["foo@example.com", "bar@example.com"]},
    "line": {"enabled": false, "token": null},
    "slack": {"enabled": true, "webhook_url": "https://hooks.slack.com/..."}
  },
  "trigger_status": ["pending", "confirmed"]
}

PUT  /api/dashboard/shops/{profile_id}/notifications
Request
{
  "updated_at": "2025-09-25T12:34:56Z",  // 楽観ロック用。最新と異なる場合は 409。
  "channels": {
    "email": {"enabled": true, "recipients": ["owner@example.com"]},
    "line": {"enabled": false, "token": null},
    "slack": {"enabled": false, "webhook_url": null}
  },
  "trigger_status": ["pending", "confirmed", "cancelled"]
}

Responses
- 200: 保存成功。最新値と `updated_at` を返却。
- 400: JSON 構造が仕様外（例: recipients が文字列）。
- 401/403: 認証 or 権限不足。店舗紐付けが無い場合を含む。
- 404: `profile_id` が存在しない or ログインユーザーと紐付いていない。
- 409: `updated_at` 不一致（他ユーザーが更新）。レスポンスには最新 `updated_at` と差分フィールド。
- 422: バリデーションエラー（チャネル宛先不足/形式不正）。

POST /api/dashboard/shops/{profile_id}/notifications/test
Request body は PUT と同構造（未保存の値で試し送信）。
- 204: テスト送信成功（本文無し）。
- 400/422: 入力不正。
- 424: 下位通知サービスで失敗した場合。`{"detail": "LINE Notify authentication failed"}` などを返す。
```

#### エラーケース UI ハンドリング

- `422` → 各フィールドにエラーテキストを表示（API の `detail` から対象フィールドを判別）。フォーム全体には「保存に失敗しました」トースト。
- `409` → モーダルで「最新の内容を取得」ボタンを出し、押下で `GET` を再実行してフォームを更新。
- `424`（テスト送信） → トーストで失敗理由を表示し、`response.detail` が `line_token_invalid` などのコードなら該当フィールドに補助テキスト。
- ネットワークエラー → 共通エラーバナーを表示し再試行リンクを提示。10 秒後に自動で閉じる。

#### 実装タスクメモ

- [ ] Profiles テーブルに通知関連列を追加するマイグレーション（null 許容、初期値空）。
- [ ] FastAPI 側に `DashboardNotificationSettings` スキーマ（Pydantic）を追加し、認証済みユーザーとプロファイルのマッピングを検証する依存性を実装。
- [ ] Next.js Dashboard に `NotificationSettingsForm` コンポーネントを新設。React Hook Form + Zod で上記バリデーションを定義し、API エラーをマージ。
- [ ] テスト送信エンドポイントは通知キューと同じパスを使い、予約 ID ダミー/`BackgroundTasks` で即時送信可否を判定する実装を流用。

#### バックエンド実装チケット案

1. **API-DB-001: Profiles 通知設定カラム追加**  
   - 作業内容: `profiles` テーブルに `notify_email_recipients (TEXT[])`, `notify_line_token (TEXT)`, `notify_slack_webhook (TEXT)`, `notify_trigger_status (TEXT[])`, `notify_channels_enabled (JSONB)` などの列を追加。既存モデル/スキーマを更新し、空配列・null の扱いを統一。  
   - 受け入れ基準: Alembic マイグレーションが適用可能で、既存データに影響しない。`models.Profile` で新列が参照できる。  
   - 依存: なし（最優先で着手）。

2. **API-DASH-002: 通知設定 API 実装**  
   - 詳細タスク:  
     1. Pydantic スキーマ定義 (`DashboardNotificationSettings`, `DashboardNotificationChannels`) を `app/schemas.py` へ追加し、メールアドレス・Slack URL・LINE トークン形式のバリデーションをカバー。  
     2. ダッシュボード用依存関数を `app/deps.py` に実装し、認証済みユーザーがアクセス可能な `profile_id` を検証。認可失敗時は `HTTPException 403/404`。  
     3. 新規ルーター `app/routers/dashboard_notifications.py` を追加し、`GET/PUT/POST test` を実装。`PUT` では `updated_at` の楽観ロック比較を行い、競合時は `409` と最新データを返す。  
     4. `POST .../test` は投入された値で `queue_reservation_notifications` に渡す前検証を共通化し、送信せずにスタブ（または後続タスクで実装予定のダミー送信）を返す構造にする。  
     5. FastAPI ルーターを `app/main.py` へ組み込み、`api/v1/dashboard` など名前空間を決定。  
     6. ユニットテスト（Pydantic バリデーション）と API テスト（401/403/404/409/422 ケース）を `app/tests` 配下に追加。  
   - 受け入れ基準: テストがグリーンで、未認証・権限外アクセスは適切な 401/403/404 を返す。  
   - 依存: API-DB-001（新カラムが必要）。

3. **API-NOTIFY-003: 予約通知処理の設定参照切り替え**  
   - 作業内容: `queue_reservation_notifications` を中心に、通知送信時に `profiles` の設定を参照するようリファクタ。チャネル別に無効化/宛先未設定時のスキップ、グローバル環境変数からのフォールバックを設計。テスト送信 API と共通化したバリデーションロジックを使用。  
   - 受け入れ基準: 既存の通知テストが改修後も成功し、新たに per-profile 設定をカバーするテストが追加される。  
   - 依存: API-DB-001, API-DASH-002（保存された設定を利用）。
