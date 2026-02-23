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

### MCP ツール定義（動的取得）
- [ ] `backend/services/mcp_client.py` に `list_tools(jwt_token)` メソッドを追加
  - MCP `tools/list` JSON-RPC メソッドを呼び出してツール一覧を取得
  - MCP 形式（`inputSchema`）→ Anthropic 形式（`input_schema`）に変換して返す
  - アプリケーション起動時にキャッシュする仕組みを追加

### 動作確認
- [ ] Python スクリプトや Flask shell で各 MCP ツールを直接呼び出して動作を確認

## 完了条件
- [ ] `get_catalogs` でコネクション一覧が取得できる
- [ ] `get_tables` で指定カタログのテーブル一覧が取得できる
- [ ] `query_data` で SQL を実行し結果が取得できる
- [ ] 別ユーザーの `accountId` では別データが返ることを確認（テナント分離）

### テスト
- [ ] `backend/tests/test_mcp_client.py` を新規作成
  - MCP クライアントの各メソッドをモック（requests/httpx）で単体テスト
  - `get_catalogs`, `get_schemas`, `get_tables`, `get_columns`, `query_data` の正常系
  - `list_tools` のレスポンスが Anthropic 形式に変換されること
  - エラーハンドリング（接続エラー・認証エラー）
- [ ] 全テスト通過確認（`python -m pytest backend/tests/ -v`）
