# Claude Code Max プラン 動作チェックリスト 📋

## チェック項目と確認状況

| # | チェック項目 | 合格ライン | 確認コマンド／場所 | 状態 |
|---|------------|-----------|------------------|------|
| 1 | Anthropic API キーを GitHub Secrets に登録 | `ANTHROPIC_API_KEY` が Settings › Secrets › Actions に表示 | [Settings > Secrets](https://github.com/yusaku0324/kakeru/settings/secrets/actions) | ⏳ |
| 2 | ワークフロー YAML にキーを流している | `env: ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}` | `.github/workflows/*.yml` | ⏳ |
| 3 | uses: が自分の fork 名 | 例：`uses: yusaku0324/claude-code-action@v1` | YAML を確認 | ⏳ |
| 4 | providers／image 設定に anthropic | `.env` → `PROVIDERS=anthropic` | `.env` / `action.yml` | ⏳ |
| 5 | Docker イメージを GHCR に push 済み | `docker pull ghcr.io/yusaku0324/claude-code-action:v1` | ローカル or Actions | ⏳ |
| 6 | ランナーで特権コンテナ許可 | `options: --privileged` | YAML と Org 設定 | ⏳ |
| 7 | Workflow permissions 設定 | `permissions: contents/packages/id-token` | YAML | ⏳ |
| 8 | Outbound で api.anthropic.com 開通 | `curl` で 200 返す | ランナー shell | ⏳ |
| 9 | Actions ログに POST /v1/messages | 200 が出る | GitHub Actions ログ | ⏳ |
| 10 | @claude メンションに応答 | Bot から返信 | Slack/Discord | ⏳ |

## 設定手順

### 1. GitHub Secrets の設定

```bash
# GitHub CLI で設定
gh secret set ANTHROPIC_API_KEY --body "sk-ant-api03-..."

# または Web UI から設定
# https://github.com/yusaku0324/kakeru/settings/secrets/actions/new
```

### 2. ワークフローの作成

```yaml
# .github/workflows/claude-code-max.yml
name: Claude Code Max
on:
  workflow_dispatch:
  issue_comment:
    types: [created]

permissions:
  contents: read
  packages: write
  id-token: write

jobs:
  claude-max:
    runs-on: ubuntu-latest
    if: contains(github.event.comment.body, '@claude')
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Claude Code Max
        uses: anthropics/claude-code-action@v1  # または fork
        with:
          anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          PROVIDERS: anthropic
          
      - name: Run Claude Analysis
        run: |
          claude analyze --model claude-3-opus-20240229 .
```

### 3. Docker イメージの準備

```dockerfile
# Dockerfile
FROM ghcr.io/anthropics/claude-code:latest

ENV PROVIDERS=anthropic
ENV MAX_TOKENS=4096

COPY . /workspace
WORKDIR /workspace
```

### 4. 接続テスト

```bash
# API接続テスト
curl -H "x-api-key: $ANTHROPIC_API_KEY" \
     -H "anthropic-version: 2023-06-01" \
     https://api.anthropic.com/v1/models

# Claude CLI テスト
claude --version
claude list-models
```

### 5. セルフホストランナーでの設定

```bash
# ランナーでの環境変数設定
echo "ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY" >> ~/.env
echo "PROVIDERS=anthropic" >> ~/.env
```

## トラブルシューティング

### エラー: API key not found
```bash
# 環境変数を確認
echo $ANTHROPIC_API_KEY
# GitHub Secrets を確認
gh secret list
```

### エラー: Permission denied
```yaml
# ワークフローに追加
options: --privileged
```

### エラー: Rate limit exceeded
```yaml
# リトライロジックを追加
- name: Run with retry
  uses: nick-invision/retry@v2
  with:
    timeout_minutes: 10
    max_attempts: 3
    command: claude analyze .
```

## 現在の状態

- [ ] GitHub Secrets に ANTHROPIC_API_KEY を設定
- [ ] ワークフロー YAML を作成
- [ ] Docker イメージをビルド・プッシュ
- [ ] 接続テストを実行
- [ ] 本番環境で動作確認

---
最終更新: 2024/01/27