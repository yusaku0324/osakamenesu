# Claude OAuth トークン取得 - 最も簡単な方法

## 手順

### 1. Claude.aiを開く
1. https://claude.ai にアクセス
2. ログインする

### 2. ブラウザのコンソールを開く
- Mac: `Cmd + Option + J`
- Windows: `Ctrl + Shift + J`

### 3. 以下のコマンドを実行

```javascript
// このコマンドをコンソールにコピペして実行
(async () => {
    const tokens = {
        access: localStorage.getItem('access_token') || 
                sessionStorage.getItem('access_token') || 
                'not-found-in-storage',
        refresh: localStorage.getItem('refresh_token') || 
                 sessionStorage.getItem('refresh_token') || 
                 'not-found-in-storage',
        expires: Date.now() + 86400000 // 24時間後
    };
    
    // Cookieもチェック
    const cookies = document.cookie.split(';');
    cookies.forEach(cookie => {
        const [key, value] = cookie.trim().split('=');
        if (key.includes('token') || key.includes('auth')) {
            console.log(`Cookie found: ${key} = ${value.substring(0, 20)}...`);
        }
    });
    
    console.log('\n🔑 GitHub Secrets:');
    console.log('==================');
    console.log(`CLAUDE_ACCESS_TOKEN=${tokens.access}`);
    console.log(`CLAUDE_REFRESH_TOKEN=${tokens.refresh}`);
    console.log(`CLAUDE_EXPIRES_AT=${tokens.expires}`);
    
    // クリップボードにコピー
    const text = `CLAUDE_ACCESS_TOKEN=${tokens.access}\nCLAUDE_REFRESH_TOKEN=${tokens.refresh}\nCLAUDE_EXPIRES_AT=${tokens.expires}`;
    await navigator.clipboard.writeText(text);
    console.log('\n✅ Copied to clipboard!');
})();
```

### 4. もしトークンが見つからない場合

#### ネットワークタブを使う方法：
1. 開発者ツールで「Network」タブを開く
2. Claude.aiでページをリフレッシュ
3. `/api/` で始まるリクエストを探す
4. Request HeadersのAuthorizationを確認

#### 手動でAPIキーを使い続ける：
現在のAPIキー認証でも十分機能するので、OAuthトークンが取得できない場合はAPIキーを使い続けることもできます。

## GitHubシークレットに設定

取得したトークンを以下のURLで設定：
https://github.com/yusaku0324/kakeru/settings/secrets/actions

1. 「New repository secret」をクリック
2. 各トークンを設定：
   - Name: `CLAUDE_ACCESS_TOKEN`
   - Value: 取得したアクセストークン
   
3. 同様に`CLAUDE_REFRESH_TOKEN`と`CLAUDE_EXPIRES_AT`も設定

## 注意事項
- トークンが「not-found-in-storage」の場合、Claude.aiの仕様変更の可能性があります
- その場合は、現在のAPIキー認証を継続して使用してください