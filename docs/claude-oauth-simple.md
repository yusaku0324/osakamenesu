# Claude Max OAuth トークン取得（簡単な手順）

## 手順

### 1. Claude.aiにログイン
https://claude.ai にアクセスしてログイン

### 2. ブラウザコンソールを開く
- Chrome/Edge: `Cmd + Option + J` (Mac) または `Ctrl + Shift + J` (Windows)
- Safari: 開発メニューを有効にしてから `Cmd + Option + C`

### 3. 以下のコマンドを実行

```javascript
// コンソールにコピペして実行
copy(JSON.stringify({
  CLAUDE_ACCESS_TOKEN: localStorage.getItem('access_token') || 
                       sessionStorage.getItem('access_token') || 
                       document.cookie.match(/access_token=([^;]+)/)?.[1] || 
                       'not-found',
  CLAUDE_REFRESH_TOKEN: localStorage.getItem('refresh_token') || 
                        sessionStorage.getItem('refresh_token') || 
                        document.cookie.match(/refresh_token=([^;]+)/)?.[1] || 
                        'not-found',
  CLAUDE_EXPIRES_AT: Date.now() + 86400000 // 24時間後
}, null, 2));
console.log('✅ トークン情報をクリップボードにコピーしました！');
```

### 4. GitHubシークレットに設定
1. https://github.com/yusaku0324/kakeru/settings/secrets/actions
2. コピーした各値を対応するシークレットに設定：
   - `CLAUDE_ACCESS_TOKEN`
   - `CLAUDE_REFRESH_TOKEN`
   - `CLAUDE_EXPIRES_AT`

## トークンが見つからない場合

### 代替手段1: ネットワークタブから確認
1. 開発者ツールの「Network」タブを開く
2. Claude.aiでページをリフレッシュ
3. `api` や `auth` を含むリクエストを探す
4. Request HeadersまたはResponseを確認

### 代替手段2: Application タブから確認
1. 開発者ツールの「Application」タブ
2. 左側メニューから以下を確認：
   - Local Storage → claude.ai
   - Session Storage → claude.ai
   - Cookies → claude.ai

## 注意
- トークンが`not-found`の場合は、APIキー認証にフォールバックします
- セキュリティのため、トークンは他人と共有しないでください