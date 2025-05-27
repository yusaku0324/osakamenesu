#!/bin/bash
# X DMBot 自動開発システム起動スクリプト

echo "🚀 X DMBot 自動開発システムを開始します..."

# 現在のディレクトリに移動
cd /Users/yusaku/Documents/GitHub/kakeru/x-dm-bot

# 1. セットアップ実行
echo "📦 環境セットアップ中..."
python setup_auto_development.py

# 2. GitHubアクションの有効化
echo "🔧 CI/CDパイプライン設定中..."
git add .github/workflows/auto-development.yml
git add scripts/
git add auto_developer.py
git add setup_auto_development.py
git commit -m "🤖 自動開発システム追加 - AI駆動型製品化開始"
git push origin main

# 3. 自動開発プロセス開始（バックグラウンド）
echo "🎯 自動開発プロセス開始..."
nohup python auto_developer.py --mode=production --target=enterprise > auto_dev.log 2>&1 &
AUTO_DEV_PID=$!
echo "自動開発プロセス PID: $AUTO_DEV_PID"

# 4. 品質監視開始
echo "📊 品質監視システム開始..."
nohup python scripts/quality_monitor.py > quality_monitor.log 2>&1 &
QUALITY_PID=$!
echo "品質監視プロセス PID: $QUALITY_PID"

# 5. WebGUI再起動（最新の変更を反映）
echo "🖥️ WebGUI再起動中..."
pkill -f "integrated_web_gui"
sleep 2
nohup python integrated_web_gui.py --port 5003 > integrated.log 2>&1 &
WEBGUI_PID=$!
echo "WebGUI PID: $WEBGUI_PID"

# 6. 監視ダッシュボード起動
echo "📈 監視ダッシュボード準備中..."
sleep 5

echo ""
echo "✅ 自動開発システムが正常に起動しました！"
echo ""
echo "📊 アクセス先:"
echo "   - WebGUI: http://localhost:5003"
echo "   - 監視ダッシュボード: http://localhost:9000"
echo ""
echo "📋 プロセス状況:"
echo "   - 自動開発: PID $AUTO_DEV_PID"
echo "   - 品質監視: PID $QUALITY_PID" 
echo "   - WebGUI: PID $WEBGUI_PID"
echo ""
echo "📂 ログファイル:"
echo "   - auto_dev.log - 自動開発ログ"
echo "   - quality_monitor.log - 品質監視ログ"
echo "   - integrated.log - WebGUIログ"
echo ""
echo "🎯 今後の流れ:"
echo "   1. 6時間以内: 複数アカウント機能の自動実装完了"
echo "   2. 24時間以内: セキュリティ強化完了"
echo "   3. 1週間以内: エンタープライズ機能完成"
echo ""
echo "🤖 システムは24/7で自動的に開発を継続します"
echo "💡 進捗は http://localhost:5003 で確認できます"