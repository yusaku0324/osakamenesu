#!/bin/bash

echo "📋 OAuth Token Update Script"
echo "==========================="
echo ""
echo "1. Open https://claude.ai in your browser and login"
echo "2. Open browser console (Cmd+Option+J on Mac)"
echo "3. Copy and paste this JavaScript code:"
echo ""
cat << 'EOF'
(async () => {
    // Try multiple methods to find tokens
    const methods = {
        localStorage: {
            access: localStorage.getItem('access_token'),
            refresh: localStorage.getItem('refresh_token')
        },
        sessionStorage: {
            access: sessionStorage.getItem('access_token'),
            refresh: sessionStorage.getItem('refresh_token')
        }
    };
    
    // Search through all storage
    const allKeys = [...Object.keys(localStorage), ...Object.keys(sessionStorage)];
    const tokenKeys = allKeys.filter(key => 
        key.includes('token') || key.includes('auth') || key.includes('claude')
    );
    
    console.log('🔍 Found keys:', tokenKeys);
    
    // Get current time + 24 hours
    const expiresAt = Date.now() + (24 * 60 * 60 * 1000);
    
    // Try to find tokens
    let accessToken = methods.localStorage.access || methods.sessionStorage.access || 'TOKEN_NOT_FOUND';
    let refreshToken = methods.localStorage.refresh || methods.sessionStorage.refresh || 'TOKEN_NOT_FOUND';
    
    console.log('\n📝 GitHub Secrets Commands:');
    console.log('==========================');
    console.log(`gh secret set ACCESSTOKEN --body "${accessToken}" --repo yusaku0324/kakeru`);
    console.log(`gh secret set REFRESHTOKEN --body "${refreshToken}" --repo yusaku0324/kakeru`);
    console.log(`gh secret set EXPIRESAT --body "${expiresAt}" --repo yusaku0324/kakeru`);
    
    if (accessToken === 'TOKEN_NOT_FOUND') {
        console.log('\n⚠️  WARNING: Tokens not found in browser storage!');
        console.log('Try checking the Network tab for API requests with Authorization headers.');
    }
})();
EOF

echo ""
echo "4. Run the generated 'gh secret set' commands to update your GitHub secrets"
echo ""
echo "Alternative: If tokens are not found, you may need to:"
echo "- Check Network tab in DevTools for Authorization headers"
echo "- Use API key authentication instead"