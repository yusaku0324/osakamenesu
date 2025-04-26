# TwExport CSV to X Queue Workflow

このリポジトリには、TwExport CSVファイルをMarkdown形式に変換し、X（旧Twitter）への投稿キューを生成するワークフローが含まれています。

## ディレクトリ構造

```
repo/
├─ drafts/                       ← ネタ置き場（Markdownファイル）
│   ├─ 2025-05-15.md
│   └─ 2025-05-16.md
├─ knowledge/                    ← Devinが読む長期ストック
│   └─ tw_crackdown_2025-05.md
├─ queue/                        ← 投稿キュー（JSONファイル）
│   └─ queue_2025-05-15.json
├─ bot/
│   ├─ csv_to_markdown.py        ← CSV → Markdown変換（Q&Aと求人を自動分類）
│   ├─ md2queue.py               ← Markdown → queue.json
│   └─ tests/
└─ .github/workflows/
    ├─ md_draft_to_queue.yml     ← Markdown → キュー変換ワークフロー
    └─ post_to_x.yml             ← X投稿ワークフロー
```

## ワークフロー

1. **Draft作成**
   - CSVファイルをMarkdownに変換（Q&Aと求人を自動分類）
   - 手動でMarkdownを編集（VS Code / GitHub Web UI）

2. **Queue生成**
   - Markdownを解析して投稿キューを生成
   - OpenAI APIを使用して140字の投稿文を自動生成
   - Q&Aと求人で異なるプロンプトを使用

3. **CI実行**
   - GitHub Actionsが毎日01:00 JSTに`md2queue.py`を実行
   - `queue_YYYY-MM-DD.json`を生成

4. **投稿**
   - `post_to_x.yml`がキューを読み込み、15分刻みでX APIに投稿

## 使用方法

### CSVからMarkdownへの変換

```bash
python bot/csv_to_markdown.py toukou_kakeru.csv
```

これにより、`drafts/YYYY-MM-DD.md`ファイルが生成されます。CSVの内容は自動的にQ&Aと求人情報に分類されます。

### MarkdownからQueueへの変換

```bash
python bot/md2queue.py
```

これにより、`queue/queue_YYYY-MM-DD.json`ファイルが生成されます。

### 全プロセスの実行

```bash
./run_workflow.sh toukou_kakeru.csv
```

## コンテンツの自動分類

CSVファイルの内容は以下の基準で自動的に分類されます：

### Q&A判定基準
- 質問マーク（?や？）を含む
- 「Q&A」「質問」「よくある質問」「FAQ」などのキーワードを含む
- 「質問」→回答 形式のパターンを含む

### Q&A形式の検出と変換
以下の形式を自動検出し、適切なMarkdown形式に変換します：
- 「質問」→回答 形式
- Q: 質問 A: 回答 形式
- 質問マーク（?や？）で終わる文とその後の回答

## Markdownフォーマット例

```markdown
# 2025-05-15 ネタ

## 🔖 都内メンエス求人情報
- **キャンセル枠4/6〜** - キャンセル枠4/6〜
  ✅アベ9万円前後の安定高収入
  ✅都内全域にルーム完備
  ✅個人オプション可能
  動画: 都内メンエス

## 📝 Q&A 情報
- **Q：「個室マッサージって風営法許可いるの？」**
  A：個室マッサージは風営法の対象となりますが、性的サービスを提供しない限り「届出制」となります。

- **Q：出稼ぎの交通費支給って本当？**
  A：店舗によりますが、多くの高級店では交通費の全額または一部を支給しています。
```

## Queue JSONフォーマット

```json
[
  {
    "text": "【都内メンエス求人】キャンセル枠4/6〜 アベ9万円前後の安定高収入✨ 都内全域にルーム完備🏠 個人オプション可能💰 #メンエス求人 #高収入 #日払い"
  },
  {
    "text": "【Q&A】個室マッサージは風営法の対象ですが、性的サービスを提供しない限り「届出制」です。詳細は各自治体の規定を確認してください。 #メンエスQ&A #風営法 #よくある質問"
  }
]
```

## 環境変数

`.env`ファイルに以下の環境変数を設定してください：

```
OPENAI_API_KEY=your_openai_api_key_here
```

## GitHub Actions

### md_draft_to_queue.yml

毎日01:00 JST（16:00 UTC）に実行され、その日のMarkdownドラフトからキューを生成します。

### post_to_x.yml

キューからツイートを読み込み、X APIを使用して投稿します。
