#!/bin/bash
# setup-claude-max.sh - Claude Code Max プラン環境のセットアップ

set -e

echo "🚀 Claude Code Max セットアップスクリプト"
echo "========================================"

# 1. API キーの確認
echo ""
echo "1️⃣ Anthropic API キーの確認"
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "❌ ANTHROPIC_API_KEY が設定されていません"
    echo "以下のコマンドで設定してください:"
    echo "  export ANTHROPIC_API_KEY='sk-ant-api03-...'"
    echo "  gh secret set ANTHROPIC_API_KEY --body 'your-api-key'"
    exit 1
else
    echo "✅ API キーが設定されています: ${ANTHROPIC_API_KEY:0:20}..."
fi

# 2. GitHub Secrets の設定
echo ""
echo "2️⃣ GitHub Secrets の設定"
if gh secret list | grep -q ANTHROPIC_API_KEY; then
    echo "✅ ANTHROPIC_API_KEY は既に GitHub Secrets に設定されています"
else
    echo "⚠️  GitHub Secrets に ANTHROPIC_API_KEY を設定します"
    read -p "設定しますか？ (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        gh secret set ANTHROPIC_API_KEY --body "$ANTHROPIC_API_KEY"
        echo "✅ 設定完了"
    fi
fi

# 3. API 接続テスト
echo ""
echo "3️⃣ Anthropic API 接続テスト"
API_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "x-api-key: $ANTHROPIC_API_KEY" \
    -H "anthropic-version: 2023-06-01" \
    https://api.anthropic.com/v1/models)

if [ "$API_RESPONSE" = "200" ]; then
    echo "✅ API 接続成功"
else
    echo "❌ API 接続失敗 (HTTP $API_RESPONSE)"
    echo "API キーを確認してください"
fi

# 4. Claude CLI のインストール確認
echo ""
echo "4️⃣ Claude CLI の確認"
if command -v claude &> /dev/null; then
    CLAUDE_VERSION=$(claude --version)
    echo "✅ Claude CLI インストール済み: $CLAUDE_VERSION"
else
    echo "⚠️  Claude CLI がインストールされていません"
    echo "インストールコマンド:"
    echo "  curl -fsSL https://cli.claude.ai/install.sh | sh"
fi

# 5. Docker 設定（オプション）
echo ""
echo "5️⃣ Docker イメージの準備（オプション）"
if command -v docker &> /dev/null; then
    echo "Docker が利用可能です"
    read -p "Claude Code Docker イメージをビルドしますか？ (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cat > Dockerfile.claude << EOF
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    curl \
    git \
    python3 \
    python3-pip

# Claude CLI インストール
RUN curl -fsSL https://cli.claude.ai/install.sh | sh

ENV PATH="/root/.claude/bin:\$PATH"
ENV PROVIDERS=anthropic

WORKDIR /workspace
EOF
        docker build -f Dockerfile.claude -t claude-code-max .
        echo "✅ Docker イメージをビルドしました"
    fi
else
    echo "Docker がインストールされていません"
fi

# 6. ワークフローの確認
echo ""
echo "6️⃣ GitHub Actions ワークフローの確認"
if [ -f ".github/workflows/claude-code-max.yml" ]; then
    echo "✅ claude-code-max.yml が存在します"
else
    echo "❌ claude-code-max.yml が見つかりません"
    echo "作成してください: .github/workflows/claude-code-max.yml"
fi

# 7. 権限の確認
echo ""
echo "7️⃣ リポジトリ権限の確認"
echo "以下を手動で確認してください:"
echo "- Settings > Actions > General > Workflow permissions"
echo "- 'Read and write permissions' が選択されているか"
echo "- 'Allow GitHub Actions to create and approve pull requests' がONか"

# 8. チェックリストの表示
echo ""
echo "📋 最終チェックリスト"
echo "===================="
echo "✅ 完了項目:"
[ ! -z "$ANTHROPIC_API_KEY" ] && echo "  - API キーの設定"
[ "$API_RESPONSE" = "200" ] && echo "  - API 接続確認"
command -v claude &> /dev/null && echo "  - Claude CLI インストール"
[ -f ".github/workflows/claude-code-max.yml" ] && echo "  - ワークフロー作成"

echo ""
echo "⏳ 要確認項目:"
echo "  - GitHub Secrets の ANTHROPIC_API_KEY"
echo "  - ワークフローの permissions 設定"
echo "  - セルフホストランナーの特権設定（該当する場合）"

echo ""
echo "🎯 次のステップ:"
echo "1. GitHub Actions で claude-code-max ワークフローを実行"
echo "2. PR や Issue で @claude メンションをテスト"
echo "3. ログを確認して動作を検証"

echo ""
echo "✅ セットアップスクリプト完了！"