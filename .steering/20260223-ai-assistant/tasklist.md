# タスクリスト: Phase 4 - AI アシスタント機能

**作成日**: 2026-02-23
**対応Issue**: [#11](https://github.com/sugimomoto/ConnectAIOEMSample/issues/11)
**ブランチ**: `feature/phase4-ai-assistant`

---

## コアフェーズ

### 1. 事前準備・環境セットアップ
- [ ] `requirements.txt` に `anthropic`, `cryptography` を追加
- [ ] `backend/config.py` に `ENCRYPTION_KEY` 環境変数設定を追加
- [ ] `backend/.env.example` に `ENCRYPTION_KEY` を追記

### 2. Claude API Key 管理（FR-AI-001）
- [ ] `backend/models.py` に `User.claude_api_key_encrypted` カラムを追加
- [ ] DB マイグレーション（または `db.create_all()` で対応）
- [ ] `backend/services/crypto_service.py` — Fernet による暗号化/復号ユーティリティ
- [ ] `backend/routes/settings.py` — API Key の取得・更新エンドポイント
- [ ] `frontend/templates/settings.html` — 設定画面 UI

### 3. MCPクライアント実装（FR-AI-004）
- [ ] `backend/services/mcp_client.py` — CData Connect AI MCP ツール呼び出しクライアント
  - `get_catalogs(account_id)`
  - `get_schemas(account_id, catalog_name)`
  - `get_tables(account_id, catalog_name, schema_name)`
  - `get_columns(account_id, catalog_name, schema_name, table_name)`
  - `query_data(account_id, query, parameters=None)`

### 4. Claude サービス実装
- [ ] `backend/services/claude_service.py` — Claude API 呼び出し（ツール使用・ストリーミング）
  - MCP ツール定義を `tools` パラメータとして渡す
  - ツール呼び出しループの実装（agentic loop）
  - SSE 形式でのストリーミング出力

### 5. チャット API エンドポイント（FR-AI-002, FR-AI-003）
- [ ] `backend/routes/ai_assistant.py`
  - `GET /ai-assistant` — チャット画面
  - `POST /ai-assistant/chat` — メッセージ送信（SSE ストリーミング）
  - `POST /ai-assistant/reset` — 会話リセット
- [ ] `backend/app.py` に Blueprint 登録

### 6. チャット画面 UI（FR-AI-002, FR-AI-003）
- [ ] `frontend/templates/ai_assistant.html`
  - カタログ選択ドロップダウン
  - チャットメッセージ一覧
  - ストリーミングレスポンスのリアルタイム表示（Alpine.js + SSE）
  - 送信フォーム
- [ ] `frontend/templates/base.html` — ナビゲーションに「AIアシスタント」「設定」メニュー追加

### 7. コア動作確認
- [ ] API Key 未設定時にチャット画面で設定誘導が表示される
- [ ] カタログを選択して自然言語質問 → AI が回答する
- [ ] カタログ未選択で質問 → AI が自律的にカタログを探索して回答する

---

## 拡張フェーズ

### 8. MCPツール呼び出し可視化（FR-AI-005）
- [ ] チャット回答にツール呼び出し情報を含める（ツール名・引数・レスポンスサマリー）
- [ ] アコーディオン UI でツール呼び出し履歴を表示

### 9. 会話コンテキスト保持（FR-AI-006）
- [ ] Flask セッションで会話履歴を保持
- [ ] 「新しい会話」ボタンでセッションをリセット

---

## 完了条件

- [ ] 自然言語でデータに質問し、AI が回答できる（コアフェーズ）
- [ ] MCPツール呼び出し可視化が動作する（拡張フェーズ）
- [ ] 会話コンテキストが保持される（拡張フェーズ）
- [ ] 既存機能（Phase 1〜3）が引き続き正常動作する
- [ ] `docs/product-requirements.md` Phase 4 の受け入れ条件をすべて満たす
