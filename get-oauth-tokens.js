// OAuth トークン取得スクリプト
// Claude.ai のコンソールで実行してください

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
    console.log(`ACCESSTOKEN=${tokens.access}`);
    console.log(`REFRESHTOKEN=${tokens.refresh}`);
    console.log(`EXPIRESAT=${tokens.expires}`);
    
    // クリップボードにコピー
    const text = `ACCESSTOKEN=${tokens.access}\nREFRESHTOKEN=${tokens.refresh}\nEXPIRESAT=${tokens.expires}`;
    await navigator.clipboard.writeText(text);
    console.log('\n✅ Copied to clipboard!');
})();