# タスクリスト: connectionId の削除とコネクション選択 UI の廃止

**作業ディレクトリ**: `.steering/20260223-fix-remove-connection-id/`
**作成日**: 2026-02-23
**関連 Issue**: #5

---

## タスク一覧

### バックエンド

- [ ] **T-01** `backend/connectai/client.py`
  - `get_catalogs(connection_id)` → `get_catalogs()`: 引数削除、`params={"connectionId": connection_id}` を削除
  - `get_schemas(connection_id, catalog_name)` → `get_schemas(catalog_name)`: 引数削除、`connectionId` を params から削除
  - `get_tables(connection_id, catalog_name, schema_name)` → `get_tables(catalog_name, schema_name)`: 同様
  - `get_columns(connection_id, catalog_name, schema_name, table_name)` → `get_columns(catalog_name, schema_name, table_name)`: 同様

- [ ] **T-02** `backend/services/metadata_service.py`
  - 各メソッドから `connection_id` 引数を削除
  - client 呼び出しも `connection_id` なしに更新

- [ ] **T-03** `backend/api/v1/metadata.py`
  - `get_catalogs`: `connection_id` の取得・バリデーションを削除
  - `get_schemas`: `connection_id` の取得・バリデーションを削除（`catalog_name` のみ必須）
  - `get_tables`: `connection_id` の取得・バリデーションを削除（`catalog_name` / `schema_name` のみ必須）
  - `get_columns`: `connection_id` の取得・バリデーションを削除（`catalog_name` / `schema_name` / `table_name` のみ必須）

### フロントエンド

- [ ] **T-04** `frontend/static/js/api-client.js`
  - `getCatalogs(connectionId)` → `getCatalogs()`: 引数削除、URL から `connection_id=` を削除
  - `getSchemas(connectionId, catalogName)` → `getSchemas(catalogName)`: 同様
  - `getTables(connectionId, catalogName, schemaName)` → `getTables(catalogName, schemaName)`: 同様
  - `getColumns(connectionId, catalogName, schemaName, tableName)` → `getColumns(catalogName, schemaName, tableName)`: 同様

- [ ] **T-05** `frontend/pages/explorer.html`
  - コネクション選択ドロップダウン（HTML）を削除
  - Alpine.js データから `connections` / `selectedConnectionId` を削除
  - `init()` を `getCatalogs()` 直接呼び出しに変更
  - `onConnectionChange()` を削除
  - `onCatalogChange()` / `onSchemaChange()` / `onTableChange()` の呼び出しから `selectedConnectionId` を削除

- [ ] **T-06** `frontend/pages/query.html`
  - T-05 と同様の変更を適用

- [ ] **T-07** `frontend/pages/data-browser.html`
  - T-05 と同様の変更を適用

### テスト修正

- [ ] **T-08** `backend/tests/conftest.py`
  - `mock_connect_ai_metadata` fixture の mock 設定から `connection_id` 引数を削除
  - `assert_called_once_with("conn-001", ...)` → `assert_called_once_with(...)` に対応

- [ ] **T-09** `backend/tests/test_metadata.py`
  - 各テストの API 呼び出しから `connection_id=conn-001` クエリパラメータを削除
  - `mock.assert_called_once_with("conn-001", ...)` → `assert_called_once_with(...)` に更新
  - `test_get_catalogs_missing_param`（`connection_id` 未指定で 400）を削除
  - 各エンドポイントの「必須パラメータ欠如で 400」テストを `catalog_name` 等の欠如に更新

### 動作確認

- [ ] **T-10** テスト実行・パス確認
  - `PYTHONPATH=$(pwd) pytest backend/tests/test_metadata.py -v` がすべて PASS すること

---

## 完了条件

- すべてのタスクが完了している
- `pytest backend/tests/test_metadata.py` が全件 PASS
- メタデータ API リクエストに `connectionId` が含まれない（API ログで確認可能）
- 各画面の初期表示でコネクション選択なしにカタログ一覧が表示される
