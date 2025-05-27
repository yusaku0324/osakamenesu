# @claude メンションが反応しない問題の改善策

## 問題の原因

1. **GitHub Actions の制限**
   - `issue_comment` イベントは新規Issueの作成時には発火しない
   - コメントを追加したときのみ発火する

2. **Claude API 統合の問題**
   - 公式のClaude GitHub Appが必要（現在は提供されていない）
   - APIキーだけではGitHubコメントに自動返信できない

## 改善案

### 1. 🔧 即効性のある修正

#### a) Issueオープン時も反応するように修正
```yaml
# .github/workflows/claude-code-max.yml に追加
on:
  issues:
    types: [opened, edited]  # 新規Issue作成時も反応
  issue_comment:
    types: [created]
```

#### b) PR コメントにも対応
```yaml
on:
  pull_request_comment:
    types: [created]
```

### 2. 🤖 代替ソリューション

#### a) GitHub Actions Bot を使った返信
```yaml
- name: Post Claude Response
  uses: actions/github-script@v7
  with:
    script: |
      const response = process.env.CLAUDE_RESPONSE;
      await github.rest.issues.createComment({
        owner: context.repo.owner,
        repo: context.repo.repo,
        issue_number: context.issue.number,
        body: `### Claude Analysis\n\n${response}\n\n---\n_Powered by Claude API_`
      });
```

#### b) Webhook ベースのソリューション
1. Vercel/Netlify Functions でWebhookエンドポイント作成
2. GitHub Webhooks で issue_comment を転送
3. Claude API を呼び出して返信

### 3. 📱 ローカル Claude CLI を活用

```bash
# Issue のコメントを取得してClaude に渡す
gh issue view 45 --json comments | \
  jq -r '.comments[-1].body' | \
  claude "このコメントに対して返信を生成してください"

# 結果をIssueに投稿
gh issue comment 45 --body "$(claude_response)"
```

### 4. 🚀 完全自動化ソリューション

#### GitHub App の作成
```javascript
// claude-bot-app.js
const { App } = require('@octokit/app');
const { Anthropic } = require('@anthropic-ai/sdk');

const app = new App({
  appId: process.env.APP_ID,
  privateKey: process.env.PRIVATE_KEY,
});

app.webhooks.on('issue_comment.created', async ({ payload }) => {
  if (payload.comment.body.includes('@claude')) {
    // Claude API 呼び出し
    const response = await anthropic.messages.create({
      model: 'claude-3-opus-20240229',
      messages: [{ role: 'user', content: payload.comment.body }]
    });
    
    // GitHub に返信
    await octokit.issues.createComment({
      owner: payload.repository.owner.login,
      repo: payload.repository.name,
      issue_number: payload.issue.number,
      body: response.content
    });
  }
});
```

## 推奨アプローチ

### 短期的解決策（すぐ実装可能）
1. ワークフローを修正して `issues: [opened]` を追加
2. 手動でコメントを追加してテスト
3. GitHub Actions の中で Claude CLI を実行

### 中期的解決策
1. Serverless Functions でWebhookを受信
2. Claude API を呼び出し
3. GitHub API で返信

### 長期的解決策
1. 専用のGitHub App を開発
2. Claude API と完全統合
3. リアルタイムでの返信

## テスト方法

1. **既存Issueにコメント追加**
   ```bash
   gh issue comment 45 --body "@claude この問題について分析してください"
   ```

2. **ワークフローログ確認**
   ```bash
   gh run list --workflow=claude-code-max.yml
   gh run view [RUN_ID] --log
   ```

3. **手動実行**
   ```bash
   gh workflow run claude-code-max.yml
   ```

## セキュリティ考慮事項

- API キーの露出を防ぐ
- レート制限の実装
- 許可されたユーザーのみ @claude を使用可能に

---

最も簡単な解決策は、Issue作成後に手動でコメントを追加することです。