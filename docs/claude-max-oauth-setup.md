# Claude Max OAuth認証セットアップ手順

## 重要な注意事項
OAuth認証を使用する場合、以下の手順で認証情報を取得する必要があります。

## 認証情報の取得方法

### 方法1: ブラウザの開発者ツールから取得
1. https://claude.ai にログイン
2. ブラウザの開発者ツールを開く（F12）
3. Application/Storage → Cookies を確認
4. 以下の値を探す：
   - セッション関連のトークン

### 方法2: Claude CLIから取得
```bash
# npmでインストールされている場合
npx claude auth login
# 認証後、以下で確認
npx claude auth status
```

### 方法3: 手動で認証トークンを生成
1. https://github.com/settings/tokens にアクセス
2. Personal access token を生成
3. 必要なスコープを選択

## GitHubシークレットの設定

### 必須シークレット
1. `CLAUDE_ACCESS_TOKEN`: アクセストークン
2. `CLAUDE_REFRESH_TOKEN`: リフレッシュトークン
3. `CLAUDE_EXPIRES_AT`: 有効期限（Unix timestamp）

### 代替方法：APIキーを使用
OAuth認証の代わりにAPIキーを使用する場合：

1. ワークフローファイルを修正：
```yaml
- name: Run Claude Code
  id: claude
  uses: yusaku0324/claude-code-action@main
  with:
    use_oauth: 'false'  # または削除
    anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
```

2. GitHubシークレットに追加：
   - `ANTHROPIC_API_KEY`: sk-ant-api03-... (既に取得済み)

## GitHub Appのインストール確認
1. https://github.com/settings/installations にアクセス
2. Claude Appがインストールされているか確認
3. 必要に応じて権限を更新

## トラブルシューティング
- ワークフローが実行されない → Actionsタブで有効化を確認
- 認証エラー → シークレットの値を再確認
- 応答がない → GitHub Appの権限を確認