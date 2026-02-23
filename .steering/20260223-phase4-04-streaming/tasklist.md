# タスクリスト: Phase 4-4 - ストリーミング対応

**作成日**: 2026-02-23
**対応Issue**: [#11](https://github.com/sugimomoto/ConnectAIOEMSample/issues/11)
**ブランチ**: `feature/phase4-ai-assistant`
**要求・設計**: [20260223-ai-assistant/](../20260223-ai-assistant/)

## 成果物
AI の回答が SSE によってリアルタイムにチャット画面に表示される

---

## タスク

### バックエンド SSE 実装
- [ ] `backend/services/claude_service.py` にストリーミング対応を追加
  - Anthropic SDK のストリーミング API（`stream()` / `with client.messages.stream()`）を使用
  - Agentic loop 中のツール呼び出しもストリーミング対応に組み込む
  - SSE フォーマット（`data: ...\n\n`）でチャンクを yield する

- [ ] `backend/routes/ai_assistant.py` のチャットエンドポイントを SSE レスポンスに変更
  - `POST /ai-assistant/chat` → `GET /ai-assistant/stream?message=...&catalog_name=...`
    （または `POST` + `EventStream` レスポンス）
  - Flask の `Response(stream_with_context(...), mimetype='text/event-stream')` を使用

### フロントエンド SSE 受信
- [ ] `frontend/templates/ai_assistant.html` を SSE 対応に更新
  - Alpine.js で `EventSource` を使って SSE を受信
  - チャンクが届くたびにメッセージをリアルタイムで追記表示
  - ストリーミング中はローディングインジケーターを表示
  - ストリーミング完了時に送信ボタンを再活性化

## 完了条件
- [ ] 質問送信後、AI の回答が文字単位でリアルタイムに表示される
- [ ] ストリーミング中は送信ボタンが無効化される
- [ ] ストリーミングエラー時にエラーメッセージが表示される
