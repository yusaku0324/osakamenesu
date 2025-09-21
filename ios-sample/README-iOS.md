最小のSwiftUIクライアントです。既存のCloud Runサーバーの `/api/chat` と通信します。

手順

1. Xcodeで新規 iOS App（SwiftUI, Swift）を作成
2. このフォルダの 4 ファイルをXcodeプロジェクトに追加
   - `AiKareshiApp.swift`
   - `ChatView.swift`
   - `Models.swift`
   - `ChatService.swift`
3. `ChatService.baseURL` をあなたの Service URL に変更
4. サーバーで `API_TOKEN` を使う場合、同じ値を `ChatService.apiToken` に設定
5. 実機/シミュレータで実行

操作

- チャット画面右上のスライダーアイコンからペルソナを変更できます。
  - スタイル/口調/冗長さ/絵文字
  - カスタム指示（自由入力）
  - temperature（0=安定, 1=発散）


補足

- サーバ側は `.env` に `API_TOKEN=...` を入れたら `ENV_KEYS=API_TOKEN npm run env:push` で反映
- 会話トーンはサーバ側 `conversation.ts` の環境変数（`REPLY_FLEX`, `ROMANCE_LEVEL`, `PERSONA_STYLE` など）で調整
- UIからのペルソナ指定をサーバに反映する方法は `docs/server-persona-guide.md` を参照
