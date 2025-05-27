# ワークフロー直接リンク

## Test Claude Code Simple ワークフロー

### 直接アクセス用URL：

```
https://github.com/yusaku0324/kakeru/actions/workflows/test-claude-simple.yml
```

### 代替方法：

1. **GitHub CLIで実行**
   ```bash
   gh workflow run test-claude-simple.yml
   ```

2. **ワークフローの一覧を確認**
   ```bash
   gh workflow list
   ```

3. **最新のプッシュを確認**
   ```bash
   git log --oneline -n 5
   ```

### ワークフローが表示されない場合の対処法：

1. **キャッシュクリア**
   - ブラウザのキャッシュをクリア
   - シークレット/プライベートウィンドウで開く

2. **ファイルの直接確認**
   - https://github.com/yusaku0324/kakeru/blob/main/.github/workflows/test-claude-simple.yml

3. **Actions権限の確認**
   - Settings > Actions > General
   - "Allow all actions and reusable workflows" が選択されているか確認

### ワークフロー内容：

```yaml
name: Test Claude Code Simple
on:
  workflow_dispatch:

jobs:
  test-claude:
    runs-on: self-hosted
    steps:
      - name: Check Claude CLI
        run: |
          echo "🤖 Testing Claude Code CLI..."
          echo "=========================="
          claude --version
          echo ""
          echo "✅ Claude Code CLI is working!"
```