# X（旧Twitter）投稿機能テストマニュアル

## 概要
このマニュアルでは、Selenium WebDriverを使用したX（旧Twitter）への自動投稿機能のテスト方法について説明します。テキスト投稿と複数動画投稿の両方のテスト方法を含みます。

## 前提条件

### 1. 必要なファイル
- 有効なクッキーファイル（`bot/niijima_cookies.json`）
- テスト用動画ファイル（複数動画テスト用）

### 2. 環境設定
- Python 3.8以上
- 必要なパッケージのインストール：
  ```bash
  pip install -r requirements.txt
  ```

## テスト方法

### 1. テキスト投稿のテスト
テキスト投稿のテストは、`test_post_niijima.py`スクリプトを使用して行います。

```bash
python test_post_niijima.py
```

このスクリプトは以下の処理を行います：
1. WebDriverの初期化
2. クッキーファイルの読み込み
3. X（旧Twitter）の投稿画面への移動
4. テキストの入力
5. 投稿ボタンのクリック
6. 投稿結果の確認

### 2. 複数動画投稿のテスト
複数動画投稿のテストは、`test_post_multiple_videos_niijima.py`スクリプトを使用して行います。

```bash
python test_post_multiple_videos_niijima.py
```

このスクリプトは以下の処理を行います：
1. WebDriverの初期化
2. クッキーファイルの読み込み
3. X（旧Twitter）の投稿画面への移動
4. テキストの入力
5. 複数の動画ファイルのアップロード
6. 投稿ボタンのクリック
7. 投稿結果の確認

### 3. モックテスト
実際のX（旧Twitter）アカウントにアクセスせずにテストを行いたい場合は、`test_mock_post.py`スクリプトを使用します。

```bash
python test_mock_post.py
```

このスクリプトは実際のWebDriverを使用せず、投稿処理をシミュレートします。

## トラブルシューティング

### 1. クッキーファイルの問題
クッキーファイル（`bot/niijima_cookies.json`）が空または無効な場合、認証に失敗します。以下の手順で確認してください：

1. クッキーファイルの存在確認：
   ```bash
   ls -la bot/niijima_cookies.json
   ```

2. クッキーファイルの内容確認：
   ```bash
   cat bot/niijima_cookies.json
   ```

3. クッキーファイルが空または無効な場合は、有効なクッキーを取得して更新する必要があります。

### 2. WebDriverの問題
WebDriverが正しく動作しない場合は、以下を確認してください：

1. Chromeのバージョンとundetected-chromedriverのバージョンの互換性
2. 必要なパッケージがすべてインストールされているか
3. ヘッドレスモードでの実行に問題がないか

### 3. ネットワークの問題
ネットワーク接続に問題がある場合、X（旧Twitter）へのアクセスに失敗することがあります。以下を確認してください：

1. インターネット接続が安定しているか
2. X（旧Twitter）のサイトにアクセスできるか
3. プロキシ設定が必要な場合は正しく設定されているか

## 安全なクリック機能

投稿処理の信頼性を高めるため、`safe_click.py`モジュールを使用しています。このモジュールは以下の特徴を持ちます：

1. 最大5回のリトライ
2. 指数バックオフ（1秒、2秒、4秒、8秒、16秒）
3. element_to_be_clickableの待機

```python
# safe_click_by_selectorの使用例
from bot.utils.safe_click import safe_click_by_selector

# CSSセレクタを使用して要素をクリック
success = safe_click_by_selector(
    driver,
    "[data-testid='tweetButton']",
    timeout=10,
    max_retries=5
)
```

## テスト結果の確認

テストが成功すると、以下のようなログが出力されます：

```
INFO - Successfully posted test message: https://x.com/niijima_account/status/1234567890123456789
```

このURLにアクセスして、投稿が正しく表示されているか確認してください。

## 注意事項

1. テストは本番環境のX（旧Twitter）アカウントに投稿します。テスト用アカウントを使用することをお勧めします。
2. クッキーファイルには認証情報が含まれているため、安全に管理してください。
3. 短時間に多数の投稿を行うと、X（旧Twitter）からレート制限を受ける可能性があります。
4. 複数動画のアップロードは、各動画のサイズと長さによって時間がかかる場合があります。
