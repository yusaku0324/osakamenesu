# Figma Bot

このリポジトリには、Figmaファイルの変数を更新し、PNGをレンダリングして投稿キューを更新する自動化システムが含まれています。

## 機能

- Figmaファイルの変数（`bannerVars.question`）を自動更新
- 1600×900のPNG画像をレンダリング
- YAMLキューファイルにPNG URLを追加
- 毎日2:00 JSTに自動実行

## ディレクトリ構造

```
figma-bot/
├─ .gitattributes            ← LFS設定
├─ designs/
│   └─ qa_banner.fig         ← .figバイナリ
├─ bot/
│   ├─ patch_and_render.py   ← Figma変数更新とレンダリングスクリプト
│   └─ tests/
├─ queue/
│   └─ queue_2025-05-28.yaml ← 投稿キュー
└─ .github/
    └─ workflows/
       └─ nightly.yml        ← 毎日2:00 JSTに実行
```

## セットアップ

### 1. Git LFSの有効化

```bash
git lfs install
git lfs track "*.fig"
```

### 2. GitHub Secretsの設定

以下のシークレットをリポジトリに設定してください：

| Name | 値 |
|------|-----|
| `FIGMA_FILE_ID` | Figma URLの`/file/xxxx`部分 |
| `FIGMA_NODE_ID` | 1600×900 FrameのnodeId |
| `FIGMA_API_KEY` | Personal Access Token (Files:Read + Write) |

### 3. 依存関係のインストール

```bash
pip install requests pyyaml
```

## 使用方法

### 手動実行

```bash
export FIGMA_API_KEY=your_api_key
export FIGMA_FILE_ID=your_file_id
export FIGMA_NODE_ID=your_node_id
python bot/patch_and_render.py
```

### 自動実行

GitHub Actionsが毎日2:00 JSTに自動的に実行します。

## テスト

```bash
python -m pytest bot/tests/test_patch_and_render.py -v
```

## 運用サイクル

1. `queue/`ディレクトリにYAMLファイルを追加
2. GitHub Actionsが夜間に実行
3. PNG URLが追加されたPRが自動作成
4. PRをマージして投稿準備完了

## 注意事項

- Figmaファイルは変数化済みで、`question`という変数名が必要です
- `.fig`ファイルはGit LFSで管理されます
- 環境変数が正しく設定されていることを確認してください
