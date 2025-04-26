# Devin Hand-off Template
リポ: https://github.com/yusaku0324/kakeru
ブランチ: feat/x-auto-post

## コーディング規約
- black: コードフォーマッター
  - 行の最大長: 88文字
  - ダブルクォート使用
  - 設定: `black --line-length=88 *.py`

- isort: インポート整理
  - 設定: `isort --profile black *.py`
  - blackと互換性のあるプロファイル使用

## 目標
- [ ] `generate_recruit_posts.py`のUnicodeEncodeError修正
- [ ] X（旧Twitter）自動投稿機能実装
- [ ] GitHub Actions追加
- [ ] テスト追加（80%以上カバレッジ）
- [ ] PR作成

## 仕様メモ
- OpenAI APIを使用して募集ツイートを生成
- X APIを使用して自動投稿
- 毎日09:30 JSTに実行
- 手動実行も可能
