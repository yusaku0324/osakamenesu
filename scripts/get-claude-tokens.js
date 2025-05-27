// Claude OAuth Token Extractor
// このスクリプトをClaude.aiのコンソールで実行してトークンを取得

console.log("Claude OAuth Token Extractor");
console.log("============================");

// LocalStorageから取得
const storage = {};
for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    if (key.toLowerCase().includes('auth') || 
        key.toLowerCase().includes('token') || 
        key.toLowerCase().includes('claude')) {
        storage[key] = localStorage.getItem(key);
    }
}

// SessionStorageから取得
const session = {};
for (let i = 0; i < sessionStorage.length; i++) {
    const key = sessionStorage.key(i);
    if (key.toLowerCase().includes('auth') || 
        key.toLowerCase().includes('token') || 
        key.toLowerCase().includes('claude')) {
        session[key] = sessionStorage.getItem(key);
    }
}

// Cookieから取得
const cookies = document.cookie.split(';').reduce((acc, cookie) => {
    const [key, value] = cookie.trim().split('=');
    if (key && (key.toLowerCase().includes('auth') || 
                key.toLowerCase().includes('token') || 
                key.toLowerCase().includes('session'))) {
        acc[key] = value;
    }
    return acc;
}, {});

console.log("\n=== LocalStorage ===");
console.log(JSON.stringify(storage, null, 2));

console.log("\n=== SessionStorage ===");
console.log(JSON.stringify(session, null, 2));

console.log("\n=== Cookies ===");
console.log(JSON.stringify(cookies, null, 2));

// ネットワークリクエストを監視してトークンを取得
console.log("\n=== Intercepting Network Requests ===");
console.log("ページをリフレッシュして、ネットワークリクエストを監視します...");

// Fetch APIをインターセプト
const originalFetch = window.fetch;
window.fetch = function(...args) {
    return originalFetch.apply(this, args).then(response => {
        const url = args[0];
        const headers = args[1]?.headers || {};
        
        // Authorizationヘッダーをチェック
        if (headers['Authorization'] || headers['authorization']) {
            console.log("\n🔑 Authorization Header Found:");
            console.log(headers['Authorization'] || headers['authorization']);
        }
        
        // レスポンスをクローンして内容を確認
        const cloned = response.clone();
        cloned.json().then(data => {
            if (data.access_token || data.refresh_token || data.token) {
                console.log("\n🎯 Token Response Found:");
                console.log(JSON.stringify({
                    access_token: data.access_token,
                    refresh_token: data.refresh_token,
                    expires_at: data.expires_at || data.expires_in,
                    token: data.token
                }, null, 2));
            }
        }).catch(() => {});
        
        return response;
    });
};

console.log("\n使い方:");
console.log("1. このスクリプトをClaude.aiのコンソールで実行");
console.log("2. ページをリフレッシュ（Cmd+R）");
console.log("3. コンソールに表示されるトークン情報を確認");
console.log("4. 必要な値をGitHubシークレットに設定");