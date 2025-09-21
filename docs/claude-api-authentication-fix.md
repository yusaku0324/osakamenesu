# Claude API Authentication Fix

## Issue
The GitHub Actions workflows were failing with an OAuth token expiration error:
```
OAuth token has expired. Please obtain a new token or refresh your existing token.
```

## Root Cause
The workflows were configured to use OAuth authentication (`use_oauth: 'true'`), but Claude's official API does not support OAuth. It only supports API key authentication.

## Solution
Updated both workflow files to use API key authentication:

### Changes Made:
1. **claude-official.yml** - Removed OAuth configuration and switched to API key
2. **claude-max.yml** - Removed OAuth configuration and switched to API key

### Before:
```yaml
with:
  use_oauth: 'true'
  claude_access_token: ${{ secrets.ACCESSTOKEN }}
  claude_refresh_token: ${{ secrets.REFRESHTOKEN }}
  claude_expires_at: ${{ secrets.EXPIRESAT }}
  github_token: ${{ secrets.GITHUB_TOKEN }}
```

### After:
```yaml
with:
  anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
  github_token: ${{ secrets.GITHUB_TOKEN }}
```

## Required Action
You need to add the `ANTHROPIC_API_KEY` secret to your GitHub repository:

1. Go to https://console.anthropic.com/settings/keys
2. Create or copy your API key
3. Go to your GitHub repository Settings → Secrets and variables → Actions
4. Add a new secret named `ANTHROPIC_API_KEY` with your API key value

## Note
The OAuth tokens extracted from Claude.ai web interface are not meant for API usage and cannot be used reliably in automated workflows. Always use the official Anthropic API key for GitHub Actions.