#!/usr/bin/env python3
"""
自動開発環境のセットアップスクリプト
"""

import os
import subprocess
import json
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AutoDevelopmentSetup:
    """自動開発環境をセットアップ"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        
    def setup(self):
        """完全なセットアップを実行"""
        logger.info("🚀 X DM Bot 自動開発環境のセットアップを開始します")
        
        # 1. ディレクトリ構造の作成
        self.create_directory_structure()
        
        # 2. 必要なパッケージのインストール
        self.install_dependencies()
        
        # 3. データベースのセットアップ
        self.setup_database()
        
        # 4. 設定ファイルの生成
        self.generate_config_files()
        
        # 5. Git フックのセットアップ
        self.setup_git_hooks()
        
        # 6. 初期テストの作成
        self.create_initial_tests()
        
        logger.info("✅ セットアップが完了しました！")
        logger.info("次のコマンドで自動開発を開始できます:")
        logger.info("  python auto_developer.py --mode=production --target=mvp")
    
    def create_directory_structure(self):
        """必要なディレクトリ構造を作成"""
        directories = [
            "scripts",
            "tests",
            "database",
            "docs",
            "logs",
            "media",
            "backups",
            ".github/workflows",
            "config",
            "templates"
        ]
        
        for dir_path in directories:
            path = self.project_root / dir_path
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"📁 ディレクトリを作成: {dir_path}")
    
    def install_dependencies(self):
        """必要な依存関係をインストール"""
        logger.info("📦 依存関係をインストール中...")
        
        additional_packages = [
            "pytest",
            "pytest-cov",
            "black",
            "flake8",
            "radon",
            "psutil",
            "websocket-client",
            "plotly",
            "dash",
            "celery",
            "redis",
            "sqlalchemy",
            "alembic"
        ]
        
        # requirements.txt に追加
        requirements_file = self.project_root / "requirements.txt"
        existing_packages = set()
        
        if requirements_file.exists():
            with open(requirements_file, 'r') as f:
                existing_packages = set(line.strip() for line in f if line.strip())
        
        with open(requirements_file, 'a') as f:
            for package in additional_packages:
                if package not in existing_packages:
                    f.write(f"{package}\n")
        
        # パッケージをインストール
        subprocess.run(["pip", "install", "-r", "requirements.txt"])
    
    def setup_database(self):
        """データベースをセットアップ"""
        logger.info("🗄️ データベースをセットアップ中...")
        
        # SQLite データベースの初期化
        db_config = {
            "type": "sqlite",
            "path": "database/x_dm_bot.db",
            "migrations_path": "database/migrations"
        }
        
        config_file = self.project_root / "config" / "database.json"
        with open(config_file, 'w') as f:
            json.dump(db_config, f, indent=2)
        
        # Alembic の初期化
        subprocess.run(["alembic", "init", "database/migrations"])
    
    def generate_config_files(self):
        """設定ファイルを生成"""
        logger.info("⚙️ 設定ファイルを生成中...")
        
        # メイン設定ファイル
        main_config = {
            "app_name": "X DM Bot",
            "version": "2.0.0",
            "environment": "development",
            "features": {
                "multiple_accounts": True,
                "real_time_dashboard": True,
                "advanced_security": True,
                "analytics_engine": True
            },
            "rate_limits": {
                "max_dms_per_hour": 20,
                "max_accounts": 10,
                "api_calls_per_minute": 60
            },
            "security": {
                "enable_2fa": True,
                "session_timeout": 3600,
                "max_login_attempts": 5
            }
        }
        
        config_file = self.project_root / "config" / "app_config.json"
        with open(config_file, 'w') as f:
            json.dump(main_config, f, indent=2)
        
        # 環境変数テンプレート
        env_template = """# X DM Bot 環境変数
DATABASE_URL=sqlite:///database/x_dm_bot.db
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
LOG_LEVEL=INFO

# セキュリティ設定
ENABLE_OAUTH=true
JWT_SECRET_KEY=your-jwt-secret
ENCRYPTION_KEY=your-encryption-key

# 外部サービス
SLACK_WEBHOOK_URL=
SENTRY_DSN=
ANALYTICS_API_KEY=
"""
        
        env_file = self.project_root / ".env.template"
        with open(env_file, 'w') as f:
            f.write(env_template)
    
    def setup_git_hooks(self):
        """Git フックをセットアップ"""
        logger.info("🔗 Git フックをセットアップ中...")
        
        pre_commit_hook = """#!/bin/bash
# Pre-commit hook for X DM Bot

echo "🔍 コード品質チェックを実行中..."

# Black でフォーマット
black . --check

# Flake8 でリンティング
flake8 . --max-line-length=100

# テストを実行
python -m pytest tests/ -v

if [ $? -ne 0 ]; then
    echo "❌ コミット前のチェックに失敗しました"
    exit 1
fi

echo "✅ すべてのチェックに合格しました"
"""
        
        hooks_dir = self.project_root / ".git" / "hooks"
        if hooks_dir.exists():
            pre_commit_file = hooks_dir / "pre-commit"
            with open(pre_commit_file, 'w') as f:
                f.write(pre_commit_hook)
            os.chmod(pre_commit_file, 0o755)
    
    def create_initial_tests(self):
        """初期テストを作成"""
        logger.info("🧪 初期テストを作成中...")
        
        test_template = '''"""
{module_name} のテスト
"""

import pytest
from unittest.mock import Mock, patch


class Test{class_name}:
    """{{class_name}} のテストクラス"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        pass
    
    def test_initialization(self):
        """初期化のテスト"""
        # TODO: 実装
        assert True
    
    def test_basic_functionality(self):
        """基本機能のテスト"""
        # TODO: 実装
        assert True
'''
        
        # 各モジュールに対してテストファイルを作成
        modules = ["main", "multi_account_manager", "twitter_poster", "integrated_web_gui"]
        
        for module in modules:
            test_file = self.project_root / "tests" / f"test_{module}.py"
            if not test_file.exists():
                class_name = ''.join(word.capitalize() for word in module.split('_'))
                content = test_template.format(
                    module_name=module,
                    class_name=class_name
                )
                with open(test_file, 'w') as f:
                    f.write(content)


if __name__ == "__main__":
    setup = AutoDevelopmentSetup()
    setup.setup()