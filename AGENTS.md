# Repository Guidelines

## プロジェクト構成とモジュール配置
主な自動化ロジックは `bot/`（`main.py` やスケジューラ、キュー操作）に集約され、共通クライアントは `services/`（API と `twitter_client`）へ、汎用関数は `utils/` に置かれています。補助スクリプトは `scripts/`、タスク定義は `tasks/` に存在します。リポジトリ横断のテストは `tests/`、モジュール固有のテストは `bot/tests/` に配置します。CI 用の軽量 Playwright ワークスペースは `apps/web/` 下にあり、実行結果は `apps/web/test-results/` に保存されます。設定サンプルやユーザーデータは `bot/config/`, `profiles/`, `queue/` にまとまっているため、編集時はサンプルとの差分を確認してください。補足資料や下書きは `docs/` と `drafts/` に整理します。

## ビルド・テスト・開発コマンド
仮想環境は `python -m venv .venv && source .venv/bin/activate` で作成し、依存関係は `pip install -e .[dev]` で導入します。軽量に確認したい場合は `pip install -r requirements.txt` でも構いません。投稿せず振る舞いを確認したい場合は `python bot/main.py --dry-run` を使用します。Python テストは `pytest`（カバレッジ確認は `pytest --cov=bot services`）で実行し、`pytest.ini` の `-q -ra` オプションが静かなログを提供します。Playwright の E2E テストは `cd apps/web && npm install && npm run test:e2e` を実行します。CI と同じ手順をローカルで試すには `task tests:pipeline-linked` や `task tests:validate-linked` を活用し、`task check:ci` で一連の事前チェックを流せます。

## コーディングスタイルと命名規則
整形は Black（行長 88）と isort の Black プロファイルを採用しているため、提出前に `black . && isort .` を実行します。Python はインデント 4 スペース、モジュール・関数は snake_case、クラスは PascalCase、定数は UPPER_SNAKE_CASE を維持します。YAML のキーはサンプルと同様に小文字＋ハイフンで統一し、`bot/config/accounts.yaml` ではキー順を崩さないよう注意します。ログ出力は `bot/utils/logger.py` 系の共通ユーティリティを使い、グローバル設定や環境変数の読み込みは既存パターンを踏襲してください。公開 API やサービス層の新規関数には型ヒントを付与します。

## テスト方針
`pytest.ini` で `tests/` と `bot/tests/` が収集対象として設定されています。キューやプロファイル関連のフィクスチャを更新する場合は既存サンプルを模範とし、異常系を網羅するため極力 `@pytest.mark.parametrize` を活用します。UI 回りの退行は `apps/web/tests/` の Playwright テストに追加し、失敗時は `apps/web/test-results/` のアーティファクトを確認します。外部 API を叩く箇所は `pytest` のモックを用いて再現し、再現不能なケースは `tests/` 配下にスキップ条件と理由をコメントで残してください。手動セットアップ（モック Cookie など）が必要な場合は PR の説明欄に手順を明記します。

## コミットとプルリクエスト
コミットメッセージは Conventional Commit 前置詞（`feat:` や `fix:` など）を踏襲し、スコープがある場合は `(bot)` のように短い識別子を追加します。PR はユーザー影響、動作確認コマンド、関連 Issue へのリンクを記載し、オートメーションを変更した場合は dry-run ログやスクリーンショットを添付してください。レビュー前に `git status` を確認し、生成ファイル（`apps/web/test-results/` など）は含めないよう注意します。`.env` や `bot/config/*.yaml` に求められるシークレットがある場合はレビューアが再現できるよう明示します。

## セキュリティと設定の注意
API キーは `.env` または `bot/config/accounts.yaml` にのみ保存し、平文でのコミットは禁止です。`bot/config/shadowban.yaml` のプロキシ設定を更新した際はスケジュール実行前に必ず疎通確認を行ってください。機密アカウント情報を共有する際は `accounts.example.yaml` を更新し、使用方法をコメントで補足します。大容量メディアは `動画/` 配下で管理し、他ディレクトリへのバイナリアップロードは避けてリポジトリ履歴を軽量に保ちましょう。
