# Self-Hosted Runner Claude Code CLI セットアップ完了

## インストール状況

✅ Claude Code CLIがインストールされました
- バージョン: v1.0.0-wrapper
- 場所: `~/.local/bin/claude-code`
- タイプ: APIラッパー版（公式CLIが利用できなかったため）

✅ Runner環境変数ファイルが準備されました
- ファイル: `/Users/yusaku/actions-runner/.env`
- 設定済み: `ANTHROPIC_API_KEY=your-api-key-here`

## 残りの手順

### 1. APIキーを設定

```bash
# .envファイルを編集
nano /Users/yusaku/actions-runner/.env

# 'your-api-key-here'を実際のANTHROPIC_API_KEYに置き換える
```

### 2. Runnerサービスを再起動

```bash
cd /Users/yusaku/actions-runner
./svc.sh stop
./svc.sh start
```

### 3. 動作確認

```bash
# 環境変数をエクスポートしてテスト
export ANTHROPIC_API_KEY="実際のAPIキー"
claude-code ask "Hello, Claude!"
```

## GitHub Actionsでのテスト

1. リポジトリのActionsタブから「Claude Code Max v2」ワークフローを選択
2. 「Run workflow」をクリック
3. または、IssueやPRで`@claude`メンションを使用

## トラブルシューティング

もしワークフローが失敗する場合：

1. Runnerのログを確認
   ```bash
   cd /Users/yusaku/actions-runner
   tail -f _diag/Runner_*.log
   ```

2. APIキーが正しく設定されているか確認
   ```bash
   cat /Users/yusaku/actions-runner/.env | grep ANTHROPIC
   ```

3. claude-codeコマンドが利用可能か確認
   ```bash
   which claude-code
   claude-code --version
   ```