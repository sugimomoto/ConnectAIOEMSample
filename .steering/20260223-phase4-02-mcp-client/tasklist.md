# タスクリスト: Phase 4-2 - MCP クライアント

**作成日**: 2026-02-23
**対応Issue**: [#11](https://github.com/sugimomoto/ConnectAIOEMSample/issues/11)
**ブランチ**: `feature/phase4-02-mcp-client`
**要求・設計**: [20260223-ai-assistant/](../20260223-ai-assistant/)

## 成果物
バックエンドから CData Connect AI MCP ツールを呼び出せる
（Claude 統合とは独立して動作確認できる）

---

## タスク

### MCP クライアント実装
- [x] `backend/services/mcp_client.py` を新規作成
  - `get_catalogs(account_id)` — カタログ一覧取得
  - `get_schemas(account_id, catalog_name)` — スキーマ一覧取得
  - `get_tables(account_id, catalog_name, schema_name)` — テーブル一覧取得
  - `get_columns(account_id, catalog_name, schema_name, table_name)` — カラム一覧取得
  - `query_data(account_id, query, parameters=None)` — SQL クエリ実行
- [x] 各ツール呼び出しで `accountId` を使いテナント分離を維持する（JWT の `sub` クレームに設定）
- [x] エラーハンドリング（接続エラー・認証エラー・クエリエラー）→ `MCPError` 例外

### MCP ツール定義（動的取得）
- [x] `MCPClient.list_tools()` メソッドを実装
  - MCP `tools/list` JSON-RPC メソッドを呼び出してツール一覧を取得
  - MCP 形式（`inputSchema`）→ Anthropic 形式（`input_schema`）に変換して返す
  - `get_mcp_tools(jwt_token)` / `invalidate_tools_cache()` でキャッシュ管理

### 動作確認
- [ ] Python スクリプトや Flask shell で各 MCP ツールを直接呼び出して動作を確認
  （実際の Connect AI アカウントが必要なため手動確認）

## 完了条件
- [ ] `get_catalogs` でコネクション一覧が取得できる（実環境確認）
- [ ] `get_tables` で指定カタログのテーブル一覧が取得できる（実環境確認）
- [ ] `query_data` で SQL を実行し結果が取得できる（実環境確認）
- [ ] 別ユーザーの `accountId` では別データが返ることを確認（テナント分離）

### テスト
- [x] `backend/tests/test_mcp_client.py` を新規作成（20 テスト）
  - `MCPClient._to_anthropic_format` — フォーマット変換（3 テスト）
  - `MCPClient.list_tools` — 正常系・エラー系（6 テスト）
  - `MCPClient.call_tool` — 正常系・エラー系（7 テスト）
  - `get_mcp_tools` / `invalidate_tools_cache` — キャッシュ動作（4 テスト）
- [x] 全テスト通過確認（`python -m pytest backend/tests/ -v`）→ 100 passed
