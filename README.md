# Kakeru - X（旧Twitter）自動投稿ツール

## 概要

Kakeruは、X（旧Twitter）に自動で投稿するためのPythonツールです。OpenAI APIを使用して募集ツイートを生成し、X APIを使用して自動投稿します。

## 機能

- OpenAI APIを使用した募集ツイートの自動生成
- X（旧Twitter）への自動投稿
- GitHub Actionsによる定期実行（毎日09:30 JST）
- 手動実行オプション

## 必要条件

- Python 3.8以上
- OpenAI API キー
- X（旧Twitter）API キー（Bearer Token）

## インストール

```bash
# リポジトリをクローン
git clone https://github.com/yusaku0324/kakeru.git
cd kakeru

# 依存パッケージをインストール
pip install -r requirements.txt

# .envファイルを作成
cp .env.example .env
# .envファイルを編集してAPIキーを設定
```

## 使用方法

```bash
# 募集ツイートを生成してXに投稿
python generate_recruit_posts.py
```

## 環境変数

`.env`ファイルに以下の環境変数を設定してください：

- `OPENAI_API_KEY`: OpenAI APIキー
- `TWITTER_BEARER_TOKEN`: X（旧Twitter）のBearer Token

## テスト

```bash
# テストを実行
pytest

# カバレッジレポート付きでテストを実行
pytest --cov=generate_recruit_posts
```

## GitHub Actions

このリポジトリには、以下の機能を持つGitHub Actionsワークフローが含まれています：

- 毎日09:30 JST（00:30 UTC）に自動実行
- 手動トリガーによる実行も可能

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。
