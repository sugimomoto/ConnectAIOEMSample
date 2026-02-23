# タスクリスト: Phase 4-2 - MCP クライアント

**作成日**: 2026-02-23
**対応Issue**: [#11](https://github.com/sugimomoto/ConnectAIOEMSample/issues/11)
**ブランチ**: `feature/phase4-ai-assistant`
**要求・設計**: [20260223-ai-assistant/](../20260223-ai-assistant/)

## 成果物
バックエンドから CData Connect AI MCP ツールを呼び出せる
（Claude 統合とは独立して動作確認できる）

---

## タスク

### MCP クライアント実装
- [ ] `backend/services/mcp_client.py` を新規作成
  - `get_catalogs(account_id)` — カタログ一覧取得
  - `get_schemas(account_id, catalog_name)` — スキーマ一覧取得
  - `get_tables(account_id, catalog_name, schema_name)` — テーブル一覧取得
  - `get_columns(account_id, catalog_name, schema_name, table_name)` — カラム一覧取得
  - `query_data(account_id, query, parameters=None)` — SQL クエリ実行
- [ ] 各ツール呼び出しで `accountId` を使いテナント分離を維持する
- [ ] エラーハンドリング（接続エラー・認証エラー・クエリエラー）

### MCP ツール定義
- [ ] `backend/services/mcp_tools.py` を新規作成
  - Claude API の `tools` パラメータ用ツール定義リスト（JSON Schema 形式）
  - 各ツールの `name`, `description`, `input_schema` を定義

### 動作確認
- [ ] Python スクリプトや Flask shell で各 MCP ツールを直接呼び出して動作を確認

## 完了条件
- [ ] `get_catalogs` でコネクション一覧が取得できる
- [ ] `get_tables` で指定カタログのテーブル一覧が取得できる
- [ ] `query_data` で SQL を実行し結果が取得できる
- [ ] 別ユーザーの `accountId` では別データが返ることを確認（テナント分離）
