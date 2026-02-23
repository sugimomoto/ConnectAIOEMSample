# タスクリスト: Phase 4-6 - 会話コンテキスト保持

**作成日**: 2026-02-23
**対応Issue**: [#11](https://github.com/sugimomoto/ConnectAIOEMSample/issues/11)
**ブランチ**: `feature/phase4-06-conversation`
**要求・設計**: [20260223-ai-assistant/](../20260223-ai-assistant/)

## 成果物
フォローアップ質問が自然に続けられる。「新しい会話」でリセットできる

---

## 実装方針の変更

当初設計では Flask セッションを使うことを想定していたが、SSE ストリーミング（Phase 4-4）の
実装時にセッション更新の制約（レスポンス開始後にクッキーを更新できない）が判明したため、
**クライアントサイドの会話履歴管理**に変更した。

| 当初設計 | 採用した方式 |
|---------|------------|
| `session['chat_history']` に蓄積 | Alpine.js の `messages` 配列で管理 |
| `POST /reset` でセッションクリア | クライアントで `messages = []` にリセット |
| ユーザー分離: Flask セッション | ユーザー分離: ブラウザ（タブ）ごとに独立 |

---

## タスク

### バックエンド
- [x] `backend/api/v1/ai_assistant.py`:
  - リクエストボディの `messages` 配列をクライアント側の履歴として受け取る（Phase 4-4 で実装）
  - サーバーは `messages + [新しいメッセージ]` を `stream_chat()` に渡す（ステートレス）
  - `POST /api/v1/ai-assistant/reset` は空レスポンスを返すのみ（クライアント側でリセット）

### フロントエンド
- [x] `frontend/pages/ai_assistant.html`:
  - `messages` 配列を Alpine.js state で管理（Phase 4-4 で実装）
  - 各リクエスト時に `messages` を送信（フォローアップ質問で履歴が引き継がれる）
  - 「新しい会話」ボタンで `messages = []` にリセット（Phase 4-4 で実装）

## 完了条件
- [x] 「前の質問の詳細を教えて」などのフォローアップ質問が正しく機能する
- [x] 「新しい会話」ボタンで会話をリセットして新しい探索を始められる
- [x] 会話履歴がユーザー間で混在しない（クライアントサイドなので本質的に分離済み）

### テスト
- [x] `backend/tests/test_ai_assistant_api.py` に会話コンテキストテストを追加
  - クライアント履歴が Claude API に渡されることを確認（Phase 4-4 で実装）
  - 2ユーザーの履歴が混在しないことを確認（`test_two_users_histories_do_not_mix`）
  - `/reset` が 200 を返すことを確認（Phase 4-4 で実装）
- [x] 全テスト通過確認（`python -m pytest backend/tests/ -v`）→ 135 passed
