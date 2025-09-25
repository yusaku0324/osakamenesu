# 大阪メンエス.com コンプライアンス & 技術施策ロードマップ

提示された 5 つの施策について、背景・優先度・具体タスクを整理し、実装オーナーおよびスケジュール感をまとめる。

## 施策一覧

| No. | 項目 | 影響/リスク/コスト | 優先度 | 主担当 | 着手スプリント |
| --- | --- | --- | --- | --- | --- |
| C-01 | 掲載・ランキングの法務ライン明文化と DB/UI 反映 | 高 / 高 / 中 | **P0** | 法務: @legal-morita<br>Backend: @suzuki.api<br>Frontend: @yuki.ui | Sprint 24-07〜24-08 |
| C-02 | 個人情報（予約フォーム）の APPI 対応 | 高 / 高 / 低〜中 | **P0** | 法務: @legal-morita<br>Backend: @taro.dev<br>Ops: @akane.ops | Sprint 24-07 |
| C-03 | 投稿/レビューのモデレーション運用整備 | 中 / 中 / 低 | **P1** | CS: @kana.cs<br>Backend: @suzuki.api | Sprint 24-09 |
| C-04 | Meilisearch wait_for_task の共通化 | 高 / 低 / 低 | **P0** | Backend: @taro.dev | Sprint 24-07 |
| C-05 | DB 接続/ロギング標準化 | 中 / 低 / 低 | **P1** | Backend: @taro.dev<br>DevOps: @akane.ops | Sprint 24-08 |

P0 施策は現行リリースリスクを軽減するため、既定の P0 バックログ（予約通知・セルフ管理）と並行して優先着手する。

## 詳細タスク

### C-01 掲載・ランキングの法務ライン明文化

**目的**: 風営法上のリスクを明確に管理し、掲載/ランキング表現が規制に抵触しないよう統制する。

#### 法務ドキュメント
- 警察庁「性風俗関連特殊営業の解釈運用基準」を参照し、以下をまとめた公開ポリシーを起草。
  - 性風俗関連（2号）の届出確認が必要なケース、通常リラクゼーションとの線引き。
  - 掲載不可/要審査表現リスト、ランキング表示における優良誤認防止指針。
- 法務レビュー → 運営代表者による承認 → `docs/policies/compliance.md` としてリポジトリに追加。

#### データモデル拡張
- `profiles` テーブルに以下のカラムを追加（Alembic マイグレーション作成）。
  - `compliance_status` (`Enum('unknown','pending','verified','rejected')`, default=`'unknown'`)
  - `fuei_category` (String, nullable, 例: '2号')
  - `fuei_office` (String, nullable)
  - `fuei_notification_no` (String, nullable)
  - `fuei_notified_at` (Date, nullable)
  - `adult_flag` (Boolean, default=`False`)
- Pydantic スキーマ、管理 API、シードツールを追随。

#### UI 表示/編集
- 管理 UI（今後のセルフ管理ダッシュボード）と現行 API で、上記フィールドの閲覧/更新を可能にする。
- ランキングカード/店舗詳細に「PR/広告」「掲載基準」「根拠情報」を表示。
  - 例: `掲載基準: 特殊営業2号 届出確認済み (大阪府公安委員会)`。
  - 条件に応じ色/バッジを切り替え、通常リラク（adult_flag=False）と区別。
- 編集フローに下書きステータスを追加し、法務チェックを経て公開するワークフローを導入。

#### 監査ログ
- `admin_change_logs` に法務確認操作のエントリを追加し、誰が `compliance_status` を変更したか追跡可能にする。

### C-02 個人情報（予約フォーム）の APPI 対応

**目的**: 個人情報保護法（APPI）に沿い、予約フォームで収集する個人データの利用・保管を適切に管理する。

#### ポリシー整備
- プライバシーポリシーを改定し、以下を明記。
  - 取得目的、利用範囲、第三者提供の有無。
  - 保管期間（例: 原則 90 日、要請があれば延長）、削除請求手続き。
  - 開示/訂正/削除の問い合わせ窓口。
- マーケティングメールは明示的なオプトイン（チェックボックス）を採用し、オプトアウト手段を記載。

#### システム実装
- `Reservation` モデルに同意タイムスタンプと同意種別を保持（`marketing_opt_in` に `consent_ts` を追加するなど改善）。
- API/フロントで同意テキストとプライバシーポリシーへのリンクを表示。
- DB 上の個人データを暗号化（PGP など）またはアプリ層で暗号化キー管理。アクセス権限を運営メンバーに限定。
- ログ出力に個人識別子を含めず、アクセス監査ログを保存。
- データ削除リクエストへの対応フロー（定型 SOP）を CS/法務と共有。

### C-03 投稿/レビューのモデレーション運用

#### ワークフロー定義
- 通報→一時非表示→審査→結果通知のステップを定義。
- FastAPI に `/reports` エンドポイントを追加し、対象（profile/diary/review）、理由、証跡を受け付ける。
- 通報受付時に対象を `status='hidden'` に更新し、管理メンバーへ通知。

#### 発信者情報の保全
- 投稿/レビュー送信時に `ip_hash`, `user_agent`, `submitted_at` を保存。
- 2022 年改正による発信者情報開示請求に備え、保存期間・開示手続きの社内 SOP を `docs-compliance.md` に追記。

### C-04 Meilisearch wait_for_task の仕組み化

- 既存の `wait_for_task` 実装を共通ユーティリティに移し、インデックス更新系関数は必ずこれを利用。
- 例: `meili.py` に `def wait_for_task(task_id: int): ...` を定義し、`index_profile`, `index_bulk`, `delete_doc` 等で呼び出す。
- 今後の改修で忘れないよう lint/テストを追加（例: テストで `wait_for_task` がモック呼び出されるか確認）。

### C-05 接続設定とロギングの標準化

- `.env` → `services/api/app/settings.py` → `env.py` の流れを再確認し、SQLAlchemy URL が環境差異なく設定されるようにする。
  - ローカル実行: `localhost:<公開ポート>`。
  - Docker compose: サービス名 `db` / `db-test` を利用。
- `alembic.ini` に標準ログ設定を追加（`[loggers]`, `[handlers]`, `[formatters]`）。
  - `fileConfig` 呼出しに `if config.config_file_name:` ガードを入れ、既存の警告を解消。
- アプリログも構造化出力（JSON）へ移行を検討。最低限 INFO/ERROR がハンドラ経由で出るようにする。

## スケジュール/レビュー体制

- P0 施策（C-01, C-02, C-04）は Sprint 24-07 で開始。セルフ管理 UI と競合しないよう、専用のサブタスクとして issue を切る。
- C-01 と C-02 は法務レビューが必須のため、週次（金曜）に @legal-morita を交えた進捗確認会を実施。
- C-03, C-05 は P1 扱い。P0 完了後の早いタイミングでキックオフ。
- ドキュメント・コード更新後は `docs-requirements.md` および `docs-backlog.md` をアップデートする運用とする。

