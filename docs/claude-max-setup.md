# Claude Max GitHub Actions セットアップガイド

## 前提条件
- ✅ claude-code-action リポジトリをフォーク済み
- ✅ claude-code-base-action リポジトリをフォーク済み

## 残りの手順

### 1. GitHub シークレットの設定

以下の3つのシークレットを設定してください：

1. リポジトリの Settings → Secrets and variables → Actions にアクセス
2. "New repository secret" をクリック
3. 以下を追加：
   - `CLAUDE_ACCESS_TOKEN`: Claude認証のアクセストークン
   - `CLAUDE_REFRESH_TOKEN`: Claude認証のリフレッシュトークン
   - `CLAUDE_EXPIRES_AT`: トークンの有効期限

### 2. 認証情報の取得方法

#### 方法A: credentials.jsonから取得
```bash
# 以下のパスを確認
~/.claude/.credentials.json
~/.config/claude/credentials.json
~/Library/Application Support/claude/credentials.json
```

#### 方法B: macOSキーチェーンから取得
1. キーチェーンアクセスを開く
2. "claude"で検索
3. 該当する項目のパスワードをコピー

#### 方法C: Claude Codeから直接取得
```bash
# Claude Codeがインストールされている場合
claude auth status
```

### 3. GitHub Appのインストール

1. https://github.com/apps/claude にアクセス
2. "Install" をクリック
3. 対象リポジトリ（kakeru）を選択
4. "Install" をクリック

### 4. 動作確認

1. このPRまたは新しいIssueで以下をコメント：
   ```
   @claude こんにちは！正常に動作していますか？
   ```

2. Claude からの応答があれば成功

## トラブルシューティング

### ワークフローが実行されない場合
- Actions タブでワークフローが有効になっているか確認
- シークレットが正しく設定されているか確認
- GitHub Appがインストールされているか確認

### 認証エラーが発生する場合
- トークンが期限切れでないか確認
- シークレット名が正確か確認（大文字小文字を含む）

## 参考リンク
- [フォークしたclaude-code-action](https://github.com/yusaku0324/claude-code-action)
- [フォークしたclaude-code-base-action](https://github.com/yusaku0324/claude-code-base-action)