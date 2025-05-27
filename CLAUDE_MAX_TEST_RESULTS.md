# Claude Code Max テスト結果 🧪

## テスト実施内容

### ✅ 完了した設定

1. **GitHub Secrets**
   - `ANTHROPIC_API_KEY` が設定済み（2025-05-27）
   
2. **ワークフローファイル**
   - `.github/workflows/claude-code-max.yml` 作成済み
   - `workflow_dispatch` トリガー設定済み
   - `issue_comment` トリガー設定済み

3. **Issue作成テスト**
   - Issue #45 を作成: https://github.com/yusaku0324/kakeru/issues/45
   - `@claude` メンション付き

## テスト手順

### 方法1: GitHub UI から実行
1. https://github.com/yusaku0324/kakeru/actions/workflows/claude-code-max.yml
2. "Run workflow" ボタンをクリック
3. パラメータを入力:
   - Task: `analyze`
   - Target: `README.md`
   - Model: `claude-3-haiku-20240307`

### 方法2: Issue コメントでテスト
1. Issue #45 にアクセス
2. コメントを追加: `@claude Please review the bot/services/twitter_client/poster.py file`

### 方法3: コマンドラインから（キャッシュクリア後）
```bash
# 少し待ってから再実行
sleep 300  # 5分待つ
gh workflow run claude-code-max.yml \
  -f task=analyze \
  -f target=README.md \
  -f model=claude-3-haiku-20240307
```

## 確認ポイント

### Actions ログで確認すべき項目：
1. ✅ API キーが正しく読み込まれているか
2. ⏳ API 接続テストが成功するか
3. ⏳ Claude CLI がインストールされるか
4. ⏳ タスクが実行されるか

### Issue での確認：
- ⏳ Claude からの応答コメントが投稿されるか

## トラブルシューティング

### "Workflow does not have 'workflow_dispatch' trigger" エラー
- GitHub のキャッシュの問題
- 解決策: 5-10分待つか、GitHub UI から実行

### API 接続エラーの場合
```bash
# ローカルでテスト
export ANTHROPIC_API_KEY="sk-ant-api03-..."
curl -H "x-api-key: $ANTHROPIC_API_KEY" \
     -H "anthropic-version: 2023-06-01" \
     https://api.anthropic.com/v1/models
```

## 現在の状態

| チェック項目 | 状態 | 備考 |
|------------|------|-----|
| API キー設定 | ✅ | Secrets に設定済み |
| ワークフロー作成 | ✅ | プッシュ済み |
| workflow_dispatch | ⏳ | GitHub キャッシュ待ち |
| issue_comment | ⏳ | Issue #45 でテスト中 |
| API 接続 | ⏳ | ワークフロー実行待ち |

---
最終更新: 2024/01/27 15:40