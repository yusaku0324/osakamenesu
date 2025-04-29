# X（旧Twitter）投稿機能マニュアル - 複数動画対応版

## 概要
このマニュアルでは、Selenium WebDriverを使用したX（旧Twitter）への自動投稿機能について説明します。特に、複数の動画を1つの投稿にまとめてアップロードする機能に焦点を当てています。

## 主要機能

### 1. 単一テキスト投稿
```python
from bot.services.twitter_client.driver_factory import create_driver
from bot.services.twitter_client.cookie_loader import load_cookies
from bot.services.twitter_client.poster import post_to_twitter

# ドライバーの作成
driver = create_driver(headless=True)

# クッキーの読み込み
load_cookies(driver, "bot/niijima_cookies.json")

# テキストの投稿
result = post_to_twitter(driver, "テスト投稿です")
```

### 2. 複数動画の同時投稿
```python
from bot.services.twitter_client.poster import post_to_twitter

# 複数の動画ファイルを指定
media_files = [
    "videos/video1.mp4",
    "videos/video2.mp4",
    "videos/video3.mp4",
    "videos/video4.mp4"
]

# 複数動画を含む投稿
result = post_to_twitter(
    driver,
    "複数の動画を含む投稿です",
    media_files=media_files
)
```

## 技術的な詳細

### 1. 安全なクリック機能
- `safe_click`関数は最大5回のリトライを行います
- クリック前に`element_to_be_clickable`を待機します
- 指数バックオフ（1秒、2秒、4秒、8秒、16秒）を使用します

### 2. 複数動画アップロードの仕組み
1. 各動画ファイルを順番にアップロード
2. アップロード完了を待機
3. すべての動画がアップロードされたら投稿を実行

### 3. エラーハンドリング
- UnicodeEncodeErrorの自動修正
- ネットワークエラーのリトライ
- タイムアウトの適切な処理

## 使用例

### 1. 基本的な投稿
```python
import os
from bot.services.twitter_client.driver_factory import create_driver
from bot.services.twitter_client.cookie_loader import load_cookies
from bot.services.twitter_client.poster import post_to_twitter

# ドライバーの初期化
driver = create_driver(headless=True)

# クッキーの読み込み
cookie_path = os.path.join(os.path.dirname(__file__), "bot", "niijima_cookies.json")
if not load_cookies(driver, cookie_path):
    print("クッキーの読み込みに失敗しました")
    driver.quit()
    exit(1)

# 投稿の実行
result = post_to_twitter(driver, "テスト投稿です")
if result["success"]:
    print(f"投稿成功: {result.get('tweet_url', 'URLなし')}")
else:
    print(f"投稿失敗: {result.get('error', '不明なエラー')}")

# ドライバーの終了
driver.quit()
```

### 2. 複数動画の投稿
```python
# 動画ファイルのリスト
video_files = [
    "videos/qa_video_1.mp4",
    "videos/qa_video_2.mp4",
    "videos/qa_video_3.mp4",
    "videos/qa_video_4.mp4"
]

# 複数動画を含む投稿
result = post_to_twitter(
    driver,
    "Q&A動画シリーズ - 4本まとめて投稿",
    media_files=video_files
)

if result["success"]:
    print(f"複数動画の投稿成功: {result.get('tweet_url', 'URLなし')}")
else:
    print(f"投稿失敗: {result.get('error', '不明なエラー')}")
```

## 注意事項

1. **動画の制限**
   - 最大4つの動画を1つの投稿に含めることができます
   - 各動画は140秒以内である必要があります
   - サポートされる形式: MP4, MOV

2. **エラー対策**
   - ネットワークエラーが発生した場合は自動的にリトライします
   - UnicodeEncodeErrorは自動的に修正されます
   - タイムアウトは適切に処理されます

3. **セキュリティ**
   - クッキーファイルは安全に保管してください
   - 認証情報を公開リポジトリにコミットしないでください

## トラブルシューティング

### 1. クッキーの読み込みエラー
- クッキーファイルのパスを確認してください
- クッキーの有効期限を確認してください
- 必要に応じてクッキーを再取得してください

### 2. 動画アップロードエラー
- ファイルパスが正しいことを確認してください
- 動画の形式とサイズを確認してください
- ネットワーク接続を確認してください

### 3. 投稿エラー
- テキストの長さが制限内であることを確認してください
- 動画の数が4つ以内であることを確認してください
- アカウントの状態を確認してください

## 更新履歴
- 2025-04-28: 複数動画投稿機能を追加
- 2025-04-28: safe_click機能を強化（5回リトライ、element_to_be_clickable待機）
- 2025-04-26: 初版作成
