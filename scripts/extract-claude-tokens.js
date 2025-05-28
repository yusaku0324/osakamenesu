// Claude.ai OAuth Token Extractor v2
// このスクリプトをClaude.aiのコンソールで実行してください

console.clear();
console.log("🔍 Claude OAuth Token Extractor v2");
console.log("===================================\n");

// すべての可能な場所からトークンを探す
const results = {
    localStorage: {},
    sessionStorage: {},
    cookies: {},
    indexedDB: []
};

// 1. LocalStorageをチェック
console.log("📦 Checking LocalStorage...");
for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    const value = localStorage.getItem(key);
    
    // トークン関連のキーを探す
    if (key.match(/token|auth|session|claude|anthropic|bearer/i)) {
        results.localStorage[key] = value;
        console.log(`  ✓ Found: ${key}`);
    }
}

// 2. SessionStorageをチェック
console.log("\n📦 Checking SessionStorage...");
for (let i = 0; i < sessionStorage.length; i++) {
    const key = sessionStorage.key(i);
    const value = sessionStorage.getItem(key);
    
    if (key.match(/token|auth|session|claude|anthropic|bearer/i)) {
        results.sessionStorage[key] = value;
        console.log(`  ✓ Found: ${key}`);
    }
}

// 3. Cookieをチェック
console.log("\n🍪 Checking Cookies...");
document.cookie.split(';').forEach(cookie => {
    const [key, value] = cookie.trim().split('=');
    if (key && key.match(/token|auth|session|claude|anthropic/i)) {
        results.cookies[key] = value;
        console.log(`  ✓ Found: ${key}`);
    }
});

// 4. IndexedDBをチェック（非同期）
console.log("\n💾 Checking IndexedDB...");
if (window.indexedDB) {
    indexedDB.databases().then(dbs => {
        dbs.forEach(db => {
            console.log(`  ℹ️ Database found: ${db.name}`);
        });
    });
}

// 5. 結果を表示
console.log("\n📋 RESULTS:");
console.log("============\n");

// GitHub Secrets形式で出力
const secrets = {
    CLAUDE_ACCESS_TOKEN: '',
    CLAUDE_REFRESH_TOKEN: '',
    CLAUDE_EXPIRES_AT: ''
};

// 既知のパターンでトークンを探す
const allData = {...results.localStorage, ...results.sessionStorage, ...results.cookies};

// アクセストークンを探す
Object.entries(allData).forEach(([key, value]) => {
    if (key.match(/access.*token|bearer/i) && value && value.length > 20) {
        secrets.CLAUDE_ACCESS_TOKEN = value;
    }
    if (key.match(/refresh.*token/i) && value && value.length > 20) {
        secrets.CLAUDE_REFRESH_TOKEN = value;
    }
    if (key.match(/expire/i) && value) {
        secrets.CLAUDE_EXPIRES_AT = value;
    }
});

// もし見つからない場合は、すべてのデータから推測
if (!secrets.CLAUDE_ACCESS_TOKEN) {
    Object.values(allData).forEach(value => {
        if (value && value.length > 100 && value.match(/^[A-Za-z0-9\-_]+$/)) {
            secrets.CLAUDE_ACCESS_TOKEN = value;
        }
    });
}

// 結果を表示
console.log("🔑 GitHub Secrets (copy these values):");
console.log("=====================================");
console.log(`CLAUDE_ACCESS_TOKEN: ${secrets.CLAUDE_ACCESS_TOKEN || 'NOT FOUND'}`);
console.log(`CLAUDE_REFRESH_TOKEN: ${secrets.CLAUDE_REFRESH_TOKEN || 'NOT FOUND'}`);
console.log(`CLAUDE_EXPIRES_AT: ${secrets.CLAUDE_EXPIRES_AT || Date.now() + 86400000}`);

// クリップボードにコピー
const secretsText = `CLAUDE_ACCESS_TOKEN=${secrets.CLAUDE_ACCESS_TOKEN || 'NOT FOUND'}
CLAUDE_REFRESH_TOKEN=${secrets.CLAUDE_REFRESH_TOKEN || 'NOT FOUND'}
CLAUDE_EXPIRES_AT=${secrets.CLAUDE_EXPIRES_AT || Date.now() + 86400000}`;

if (navigator.clipboard) {
    navigator.clipboard.writeText(secretsText).then(() => {
        console.log("\n✅ Secrets copied to clipboard!");
    });
}

// 詳細データも表示
console.log("\n📊 Detailed Data:");
console.log("=================");
console.log(JSON.stringify(results, null, 2));

// ネットワークリクエストを監視する方法も提供
console.log("\n💡 Alternative Method:");
console.log("====================");
console.log("1. Open Network tab in DevTools");
console.log("2. Refresh the page");
console.log("3. Look for requests to:");
console.log("   - /api/auth/*");
console.log("   - /api/session/*");
console.log("   - Any request with Authorization header");
console.log("\n4. Check Request Headers for 'Authorization: Bearer [token]'");
console.log("5. Check Response for tokens in JSON");