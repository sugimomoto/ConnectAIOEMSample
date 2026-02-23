# タスクリスト: Phase 4-3 - チャット基本動作

**作成日**: 2026-02-23
**対応Issue**: [#11](https://github.com/sugimomoto/ConnectAIOEMSample/issues/11)
**ブランチ**: `feature/phase4-ai-assistant`
**要求・設計**: [20260223-ai-assistant/](../20260223-ai-assistant/)

## 成果物
自然言語で質問 → AI が MCP 経由でデータにアクセスして回答できる
（ストリーミングなし・レスポンス一括返却）

---

## タスク

### Claude サービス実装
- [ ] `backend/services/claude_service.py` を新規作成
  - ユーザーの Claude API Key を使って Anthropic SDK でリクエスト
  - MCP ツール定義（`mcp_tools.py`）を `tools` パラメータとして渡す
  - Agentic loop の実装（Claude がツール呼び出しを返したら MCP クライアントを呼び出し、結果を Claude に返す繰り返し）
  - 最終的なテキスト回答を返す

### チャット API エンドポイント
- [ ] `backend/routes/ai_assistant.py` を新規作成
  - `GET /ai-assistant` — チャット画面レンダリング
  - `POST /ai-assistant/chat` — メッセージ送信（一括レスポンス版）
    - リクエスト: `{ "message": "...", "catalog_name": "..." }`
    - レスポンス: `{ "answer": "...", "tool_calls": [...] }`
  - `POST /ai-assistant/reset` — 会話リセット
- [ ] `backend/app.py` に Blueprint 登録

### チャット画面 UI
- [ ] `frontend/templates/ai_assistant.html` を新規作成
  - カタログ選択ドロップダウン（Connect AI から動的取得）
  - チャットメッセージ一覧（ユーザー・アシスタントの吹き出し）
  - 送信フォーム
  - API Key 未設定時の設定誘導メッセージ

### ナビゲーション
- [ ] `frontend/templates/base.html` に「AI アシスタント」メニューを追加

## 完了条件
- [ ] メニューから AI アシスタント画面に直接遷移できる
- [ ] カタログを選択して質問 → AI が回答する（非ストリーミング）
- [ ] カタログ未選択で質問 → AI が自律的にカタログを探索して回答する
- [ ] API Key 未設定時に設定画面への誘導が表示される

### テスト
- [ ] `backend/tests/test_claude_service.py` を新規作成
  - Anthropic SDK をモックして `claude_service` の単体テスト
  - Agentic loop が正しくツール呼び出し→結果送信を繰り返すこと
  - API Key 未設定時に適切なエラーを返すこと
- [ ] `backend/tests/test_ai_assistant_api.py` を新規作成
  - `POST /api/v1/ai-assistant/chat` の正常系・異常系
  - 未ログイン時 401 が返ること
  - API Key 未設定時に 422 など適切なエラーが返ること
- [ ] 全テスト通過確認（`python -m pytest backend/tests/ -v`）
