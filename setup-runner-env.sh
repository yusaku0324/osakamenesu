#!/bin/bash

# GitHub Actions Self-Hosted Runner環境変数設定スクリプト

echo "GitHub Actions Self-Hosted Runner 環境変数設定"
echo "============================================="
echo ""

# Runnerディレクトリを探す
RUNNER_DIR=""
if [ -d "$HOME/actions-runner" ]; then
    RUNNER_DIR="$HOME/actions-runner"
elif [ -d "$HOME/_work/_actions-runner" ]; then
    RUNNER_DIR="$HOME/_work/_actions-runner"
elif [ -d "/Users/yusaku/runner" ]; then
    RUNNER_DIR="/Users/yusaku/runner"
else
    echo "Runnerディレクトリが見つかりません。"
    echo "手動で設定してください。"
    exit 1
fi

echo "Runnerディレクトリ: $RUNNER_DIR"

# .env ファイルに環境変数を追加
ENV_FILE="$RUNNER_DIR/.env"

# バックアップを作成
if [ -f "$ENV_FILE" ]; then
    cp "$ENV_FILE" "$ENV_FILE.backup.$(date +%Y%m%d_%H%M%S)"
    echo "既存の.envファイルをバックアップしました"
fi

# ANTHROPIC_API_KEYが既に設定されているか確認
if [ -f "$ENV_FILE" ] && grep -q "ANTHROPIC_API_KEY" "$ENV_FILE"; then
    echo "ANTHROPIC_API_KEYは既に設定されています"
    echo "更新する場合は、$ENV_FILE を編集してください"
else
    # 環境変数を追加
    echo "" >> "$ENV_FILE"
    echo "# Claude Code CLI" >> "$ENV_FILE"
    echo "ANTHROPIC_API_KEY=your-api-key-here" >> "$ENV_FILE"
    
    echo ""
    echo "環境変数を追加しました: $ENV_FILE"
    echo ""
    echo "重要: 以下の手順を実行してください："
    echo "1. $ENV_FILE を編集して、'your-api-key-here'を実際のAPIキーに置き換える"
    echo "2. Runnerサービスを再起動する:"
    echo "   cd $RUNNER_DIR"
    echo "   ./svc.sh stop"
    echo "   ./svc.sh start"
fi

# 現在の環境変数も設定（テスト用）
echo ""
echo "現在のシェルでテストする場合："
echo "export ANTHROPIC_API_KEY='your-api-key-here'"
echo "claude-code ask 'Hello, Claude!'"