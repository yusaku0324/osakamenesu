# X（旧Twitter）投稿機能マニュアル

## 目次
1. [概要](#概要)
2. [セットアップ手順](#セットアップ手順)
3. [使用方法](#使用方法)
4. [エラー対応](#エラー対応)
5. [トラブルシューティング](#トラブルシューティング)
6. [よくある質問](#よくある質問)

## 概要

このマニュアルでは、niijimaアカウントを使用したX（旧Twitter）への自動投稿機能について説明します。この機能は、メンズエステの求人情報を自動的に投稿するために設計されています。

### 主な機能
- 自動投稿機能
- メディア（画像・動画）のアップロード
- UnicodeEncodeErrorの自動修正
- 重複投稿の防止
- エラーハンドリングとリトライ機能

## セットアップ手順

### 1. 環境準備

#### 必要なパッケージのインストール
```bash
pip install -r requirements.txt
```

#### 必要なパッケージ一覧
- selenium
- undetected-chromedriver
- python-dotenv
- openai
- tweepy
- pyyaml
- schedule
- pyperclip

### 2. 認証情報の設定

#### .envファイルの作成
プロジェクトルートに`.env`ファイルを作成し、以下の情報を設定します：

```
OPENAI_API_KEY=your_openai_api_key
TWITTER_BEARER_TOKEN=your_twitter_bearer_token
FIGMA_TOKEN=your_figma_token
FIGMA_FILE_ID=your_figma_file_id
```

#### Cookieファイルの準備
niijimaアカウントのCookieファイルを`bot/niijima_cookies.json`に配置します。

### 3. GitHub Actionsの設定

#### シークレットの設定
GitHubリポジトリの設定で以下のシークレットを追加します：
- `OPENAI_API_KEY`
- `TWITTER_BEARER_TOKEN`
- `FIGMA_TOKEN`
- `FIGMA_FILE_ID`

## 使用方法

### 1. 手動投稿

#### テスト投稿の実行
```bash
python test_post_niijima.py
```

#### 求人投稿の生成と投稿
```bash
python generate_recruit_posts.py
```

### 2. 自動投稿（GitHub Actions）

#### 定期実行
毎日09:30 JSTに自動実行されます。

#### 手動実行
GitHubのActionsタブから「Post to X」ワークフローを手動で実行できます。

### 3. 複数メディアの投稿

#### YAMLファイルでの指定
`queue/queue_YYYY-MM-DD.yaml`ファイルで複数メディアを指定できます：

```yaml
posts:
  - text: "投稿テキスト"
    media:
      - path: "path/to/image1.jpg"
        type: "image"
      - path: "path/to/video1.mp4"
        type: "video"
```

## エラー対応

### 1. UnicodeEncodeError

#### 自動修正機能
システムは自動的に標準出力のエンコーディングをUTF-8に設定します：

```python
def ensure_utf8_encoding():
    """標準出力のエンコーディングをUTF-8に設定する"""
    try:
        if hasattr(sys.stdout, 'encoding') and sys.stdout.encoding.lower() != 'utf-8':
            sys.stdout = io.TextIOWrapper(
                sys.stdout.buffer, encoding='utf-8', line_buffering=True
            )
        return True
    except Exception as e:
        logger.error(f"エンコーディング変更中にエラーが発生しました: {e}")
        return False
```

### 2. 投稿失敗時のリトライ

#### リトライ機能
投稿が失敗した場合、システムは自動的に3回までリトライを試みます：

```python
@retry(max_attempts=3, delay=5, backoff=2)
def post_with_retry(driver, text, media_url=None):
    """リトライ機能付きの投稿関数"""
    return post_to_twitter(driver, text, media_url)
```

### 3. Cookie認証エラー

#### Cookie更新手順
1. ブラウザでXにログイン
2. 開発者ツールを開く（F12）
3. Applicationタブ → Cookies → https://x.com
4. すべてのCookieをJSON形式でエクスポート
5. `bot/niijima_cookies.json`を更新

## トラブルシューティング

### 1. 投稿が失敗する場合

#### チェックリスト
- [ ] インターネット接続を確認
- [ ] Cookieファイルが最新か確認
- [ ] APIキーが正しく設定されているか確認
- [ ] ログファイルでエラー内容を確認

### 2. メディアアップロードが失敗する場合

#### 確認事項
- ファイルサイズ制限（画像: 5MB以下、動画: 512MB以下）
- サポートされているファイル形式（画像: JPG, PNG, GIF、動画: MP4）
- ファイルパスが正しいか確認

### 3. GitHub Actionsが失敗する場合

#### デバッグ手順
1. Actionsタブでエラーログを確認
2. シークレットが正しく設定されているか確認
3. ワークフローファイルの構文を確認

## よくある質問

### Q1: 複数アカウントで投稿できますか？
A: はい、`accounts.yaml`ファイルで複数アカウントを設定できます。

### Q2: 投稿時間を変更できますか？
A: はい、`.github/workflows/post-to-x.yml`のcron設定を変更することで可能です。

### Q3: 投稿内容をカスタマイズできますか？
A: はい、`generate_recruit_posts.py`のプロンプトを編集することで可能です。

### Q4: エラーログはどこで確認できますか？
A: ローカル実行時はコンソール出力、GitHub Actions実行時はActionsタブのログで確認できます。

### Q5: 重複投稿を防ぐ仕組みはありますか？
A: はい、`PostDeduplicator`クラスが投稿内容のハッシュ値を保存し、重複を防止します。

## サポート

問題が解決しない場合は、以下の情報を添えてサポートにお問い合わせください：
- エラーメッセージの全文
- 実行環境（OS、Pythonバージョン）
- 実行したコマンド
- 関連するログファイル

---

最終更新日: 2025年4月28日
