# タスクリスト: Phase 4-3 - チャット基本動作

**作成日**: 2026-02-23
**対応Issue**: [#11](https://github.com/sugimomoto/ConnectAIOEMSample/issues/11)
**ブランチ**: `feature/phase4-03-chat-basic`
**要求・設計**: [20260223-ai-assistant/](../20260223-ai-assistant/)

## 成果物
自然言語で質問 → AI が MCP 経由でデータにアクセスして回答できる
（ストリーミングなし・レスポンス一括返却）

---

## タスク

### Claude サービス実装
- [x] `backend/services/claude_service.py` を新規作成
  - ユーザーの Claude API Key を使って Anthropic SDK でリクエスト
  - MCP ツール定義（`get_mcp_tools`）を `tools` パラメータとして渡す
  - Agentic loop の実装（tool_use → MCP 呼び出し → tool_result を最大10回繰り返す）
  - 最終的なテキスト回答とツール呼び出しログを返す

### チャット API エンドポイント
- [x] `backend/api/v1/ai_assistant.py` を新規作成
  - `GET /ai-assistant` — チャット画面レンダリング
  - `POST /api/v1/ai-assistant/chat` — メッセージ送信（一括レスポンス版）
    - リクエスト: `{ "message": "...", "catalog_name": "..." }`
    - レスポンス: `{ "answer": "...", "tool_calls": [...] }`
  - `POST /api/v1/ai-assistant/reset` — 会話リセット
- [x] `backend/api/v1/__init__.py` に `ai_assistant` モジュールを追加

### チャット画面 UI
- [x] `frontend/pages/ai_assistant.html` を新規作成
  - カタログ選択ドロップダウン（Connect AI から動的取得）
  - チャットメッセージ一覧（ユーザー・アシスタントの吹き出し）
  - ツール呼び出しアコーディオン（展開/折りたたみ）
  - 送信フォーム（Enter 送信 · Shift+Enter 改行）
  - API Key 未設定時の設定誘導メッセージ
- [x] `frontend/static/js/api-client.js` に `chatWithAI` / `resetChat` を追加

### ナビゲーション
- [x] `frontend/static/js/header.js` に「AI アシスタント」リンクは実装済み（変更不要）

## 完了条件
- [x] メニューから AI アシスタント画面に遷移できる
- [ ] カタログを選択して質問 → AI が回答する（実環境確認）
- [ ] カタログ未選択で質問 → AI が自律的にカタログを探索して回答する（実環境確認）
- [ ] API Key 未設定時に設定画面への誘導が表示される（実環境確認）

### テスト
- [x] `backend/tests/test_claude_service.py` を新規作成（14 テスト）
  - `_block_to_dict` 変換（3テスト）
  - end_turn 正常系（6テスト）
  - tool_use → MCP 呼び出し → tool_result フロー（4テスト）
  - 会話履歴の引き渡し（1テスト）
- [x] `backend/tests/test_ai_assistant_api.py` を新規作成（13 テスト）
  - 認証チェック（3テスト）
  - バリデーション（3テスト）
  - チャット正常系（4テスト）
  - セッション管理（3テスト）
- [x] 全テスト通過確認（`python -m pytest backend/tests/ -v`）→ 127 passed
