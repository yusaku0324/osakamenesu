# X DM Bot

X (Twitter) の DM を自動化するための Python ボットです。特定のキーワードを含む最新のツイートを検索し、投稿者に自動的に DM を送信します。

## 機能

- 🔍 リアルタイムツイート検索（1分以内の新着ツイート）
- 📨 自動 DM 送信
- 🛡️ アンチ検出機能（undetected-chromedriver 使用）
- ⏱️ レート制限管理
- 📝 複数のキャンペーン管理
- 🚫 除外リスト機能
- 📊 詳細なロギング

## セットアップ

### 1. 必要な環境

- Python 3.8+
- Chrome ブラウザ
- Chrome Driver（自動でダウンロードされます）

### 2. インストール

```bash
# リポジトリをクローン
git clone <repository-url>
cd x-dm-bot

# 仮想環境を作成（推奨）
python -m venv venv
source venv/bin/activate  # macOS/Linux
# または
venv\Scripts\activate  # Windows

# 依存関係をインストール
pip install -r requirements.txt
```

### 3. 設定

#### .env ファイルの設定

`.env` ファイルを作成し、X の認証情報を設定します：

```env
X_USERNAME=your_username
X_PASSWORD=your_password
```

#### config.json の設定

`config.json` でキャンペーンやレート制限を設定します：

```json
{
  "campaigns": [
    {
      "name": "キャンペーン名",
      "keywords": ["検索キーワード1", "検索キーワード2"],
      "message_templates": [
        "メッセージテンプレート1",
        "メッセージテンプレート2"
      ],
      "check_interval": 300,
      "active": true
    }
  ]
}
```

## 使用方法

```bash
# ボットを起動
python main.py
```

## メッセージテンプレート変数

メッセージテンプレートでは以下の変数が使用できます：

- `{username}` - ツイート投稿者のユーザー名
- `{keyword}` - 検索に使用されたキーワード
- `{time_ago}` - ツイートが投稿されてからの秒数
- `{tweet_text}` - ツイートの本文（最初の50文字）

## 注意事項

- X の利用規約を遵守してください
- 過度な DM 送信はアカウント制限の原因となる可能性があります
- レート制限を適切に設定してください
- プロキシの使用を検討してください

## トラブルシューティング

### ログインできない場合

1. 認証情報が正しいか確認
2. 2要素認証が有効な場合は、一時的に無効化
3. アカウントがロックされていないか確認

### DM が送信されない場合

1. 相手の DM 設定を確認
2. レート制限に達していないか確認
3. ログファイルでエラーを確認

## ライセンス

このプロジェクトは MIT ライセンスの下で公開されています。