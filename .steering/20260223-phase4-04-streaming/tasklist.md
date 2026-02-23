# タスクリスト: Phase 4-4 - ストリーミング対応

**作成日**: 2026-02-23
**対応Issue**: [#11](https://github.com/sugimomoto/ConnectAIOEMSample/issues/11)
**ブランチ**: `feature/phase4-04-streaming`
**要求・設計**: [20260223-ai-assistant/](../20260223-ai-assistant/)

## 成果物
AI の回答が SSE によってリアルタイムにチャット画面に表示される

---

## タスク

### バックエンド SSE 実装
- [x] `backend/services/claude_service.py` にストリーミング対応を追加
  - Anthropic SDK のストリーミング API（`with client.messages.stream()`）を使用
  - Agentic loop 中のツール呼び出しもストリーミング対応に組み込む
  - `(event_type, data)` タプルを yield するジェネレーター（`stream_chat()`）として実装

- [x] `backend/api/v1/ai_assistant.py` のチャットエンドポイントを SSE レスポンスに変更
  - `POST /api/v1/ai-assistant/chat` → `text/event-stream` レスポンス
  - Flask の `Response(stream_with_context(...), mimetype='text/event-stream')` を使用
  - セッション管理を廃止し、クライアントサイドの会話履歴（`messages` フィールド）に移行

### フロントエンド SSE 受信
- [x] `frontend/pages/ai_assistant.html` を SSE 対応に更新
  - `fetch` + `ReadableStream` で SSE を受信（`EventSource` は POST 非対応のため）
  - `text_delta` イベントでトークンをリアルタイム追記表示
  - `tool_start` イベントでツール呼び出しアコーディオンに追加
  - ストリーミング中はカーソル（▌）表示とボタン無効化
  - ストリーミング完了・エラー時に適切な状態リセット
  - 会話履歴を Alpine.js state で管理（リクエスト時に `messages` として送信）

## 完了条件
- [x] 質問送信後、AI の回答が文字単位でリアルタイムに表示される
- [x] ストリーミング中は送信ボタンが無効化される
- [x] ストリーミングエラー時にエラーメッセージが表示される

### テスト
- [x] `backend/tests/test_claude_service.py` に `stream_chat` テストを追加（5テスト）
  - text_delta イベント yield
  - done イベントと完全な回答
  - tool_start / tool_result イベント + agentic ループ
  - 例外発生時の error イベント
  - MCP エラー時の tool_result エラー内容
- [x] `backend/tests/test_ai_assistant_api.py` を SSE 対応に更新（13テスト）
  - auth チェック（3テスト）
  - バリデーション（3テスト）
  - SSE ストリーム正常系（5テスト）
  - クライアントサイド履歴（3テスト）
- [x] 全テスト通過確認（`python -m pytest backend/tests/ -v`）→ 133 passed
