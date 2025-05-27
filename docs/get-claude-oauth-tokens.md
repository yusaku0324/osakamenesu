# Claude Max OAuth トークンの取得方法

## 方法1: ブラウザの開発者ツールから取得

1. https://claude.ai にログイン
2. ブラウザの開発者ツールを開く（F12またはCmd+Option+I）
3. **Network**タブを選択
4. ページをリフレッシュ（Cmd+R）
5. Filterに「auth」または「token」と入力
6. APIリクエストを探して、以下を確認：
   - `Authorization`ヘッダー
   - レスポンス内の`access_token`、`refresh_token`、`expires_at`

## 方法2: Local Storageから取得

1. https://claude.ai にログイン
2. 開発者ツールを開く
3. **Application**タブ → **Local Storage** → `https://claude.ai`
4. 以下のキーを探す：
   - `auth_token` または類似のキー
   - `refresh_token`
   - `token_expires`

## 方法3: Cookieから取得

1. 開発者ツールの**Application**タブ
2. **Cookies** → `https://claude.ai`
3. 認証関連のCookieを探す

## GitHubシークレットに設定

取得した値を以下のシークレットとして設定：
- `CLAUDE_ACCESS_TOKEN`: アクセストークン
- `CLAUDE_REFRESH_TOKEN`: リフレッシュトークン  
- `CLAUDE_EXPIRES_AT`: 有効期限（Unix timestamp）

## 注意事項

- トークンは定期的に更新が必要な場合があります
- セキュリティのため、トークンは他人と共有しないでください
- 不明な場合は、APIキー認証の使用を検討してください