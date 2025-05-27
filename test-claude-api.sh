#!/bin/bash
# Claude API接続テストスクリプト

echo "🧪 Claude API 接続テスト"
echo "======================="

# GitHub Secretsから取得したAPIキーでテスト
# 注: 実際のAPIキーは手動で設定してください
ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-sk-ant-api03-XXXXXXXX}"

echo "1. API接続テスト"
echo "----------------"
curl -s -X GET \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  https://api.anthropic.com/v1/models | jq -r '.models[0].id' || echo "❌ API接続失敗"

echo ""
echo "2. メッセージ送信テスト"
echo "----------------------"
curl -s -X POST \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  https://api.anthropic.com/v1/messages \
  -d '{
    "model": "claude-3-haiku-20240307",
    "max_tokens": 100,
    "messages": [{
      "role": "user",
      "content": "Say hello in one sentence."
    }]
  }' | jq -r '.content[0].text' || echo "❌ メッセージ送信失敗"

echo ""
echo "3. Claude CLIテスト"
echo "------------------"
if command -v claude &> /dev/null; then
    claude --version || echo "❌ Claude CLI エラー"
else
    echo "❌ Claude CLI not installed"
fi

echo ""
echo "テスト完了"