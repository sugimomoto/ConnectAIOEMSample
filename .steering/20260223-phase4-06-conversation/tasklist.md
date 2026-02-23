# タスクリスト: Phase 4-6 - 会話コンテキスト保持

**作成日**: 2026-02-23
**対応Issue**: [#11](https://github.com/sugimomoto/ConnectAIOEMSample/issues/11)
**ブランチ**: `feature/phase4-ai-assistant`
**要求・設計**: [20260223-ai-assistant/](../20260223-ai-assistant/)

## 成果物
フォローアップ質問が自然に続けられる。「新しい会話」でリセットできる

---

## タスク

### バックエンド: セッション管理
- [ ] `backend/routes/ai_assistant.py` で Flask セッションを使って会話履歴を管理
  - `session['chat_history']` に messages 配列（user / assistant / tool_use / tool_result）を蓄積
  - チャットリクエスト時に既存履歴を Claude API に渡す
  - ツール呼び出し・レスポンスも履歴に含める（agentic loop の完全な記録）
- [ ] `POST /ai-assistant/reset` で `session['chat_history']` をクリア

### フロントエンド: 会話リセット
- [ ] `frontend/templates/ai_assistant.html` に「新しい会話」ボタンを追加
  - クリック時に `/ai-assistant/reset` を呼び出す
  - 画面のチャット表示もクリアする
- [ ] カタログ切り替え時の会話継続・リセットの動作を確認・調整

## 完了条件
- [ ] 「前の質問の詳細を教えて」などのフォローアップ質問が正しく機能する
- [ ] 「新しい会話」ボタンで会話をリセットして新しい探索を始められる
- [ ] 会話履歴がセッション間で混在しない（ユーザーごとに分離されている）

### テスト
- [ ] 会話コンテキスト保持のテスト
  - 2回目のメッセージ送信時に前の会話履歴が Claude API に渡されること
  - `POST /api/v1/ai-assistant/reset` でセッションがクリアされること
  - 別ユーザーの会話履歴が混在しないこと（セッション分離）
- [ ] 全テスト通過確認（`python -m pytest backend/tests/ -v`）
