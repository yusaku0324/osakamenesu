# GitHub で @claude に反応させる設定

## 問題
GitHubのPRコメントで`@claude`とメンションしても反応しない

## 解決方法

### 1. Claude GitHub App のインストール
1. [Claude for GitHub](https://github.com/apps/claude-ai) にアクセス
2. "Install" をクリック
3. リポジトリを選択（kakeru）
4. 権限を確認して承認

### 2. .github/claude.yml の設定
リポジトリに設定ファイルを追加：

```yaml
# .github/claude.yml
version: 1
rules:
  - trigger: "mention"
    action: "review"
    
  - trigger: "pr_opened"
    action: "auto_review"
    
settings:
  auto_review: true
  respond_to_mentions: true
  languages:
    - python
    - javascript
```

### 3. GitHub Actions ワークフローの追加
```yaml
# .github/workflows/claude-review.yml
name: Claude PR Review
on:
  pull_request:
    types: [opened, synchronize]
  issue_comment:
    types: [created]

jobs:
  claude-review:
    if: contains(github.event.comment.body, '@claude')
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Request Claude Review
        uses: anthropics/claude-github-action@v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          claude-api-key: ${{ secrets.CLAUDE_API_KEY }}
```

### 4. 代替方法：Claude Code CLI を使用

現在の環境では、以下のコマンドでPRをレビューできます：

```bash
# PRの内容を取得してClaudeでレビュー
gh pr view 44 --json files,body,additions,deletions | claude "このPRをレビューしてください"

# 特定のファイルをレビュー
gh pr diff 44 | claude "この差分をレビューしてください"
```

### 5. 手動でのレビュー依頼

1. PR画面で "Files changed" タブを開く
2. 変更内容をコピー
3. Claude.ai でレビューを依頼
4. 結果をPRにコメント

## 注意事項

- GitHub Apps の Claude AI が利用可能な場合のみ`@claude`が機能します
- 現在は Claude Code CLI を使用したローカルレビューが推奨されます
- セキュリティのため、APIキーは環境変数で管理してください