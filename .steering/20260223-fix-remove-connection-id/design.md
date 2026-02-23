# 設計書: connectionId の削除とコネクション選択 UI の廃止

**作業ディレクトリ**: `.steering/20260223-fix-remove-connection-id/`
**作成日**: 2026-02-23
**関連 Issue**: #5

---

## 1. 変更方針

全スタック（client → service → api → frontend）から `connection_id` / `connectionId` を削除する。
変更は独立した層ごとに行い、テストも同時に修正する。

```
frontend/pages/*.html              ← コネクション選択 UI の削除
        ↕ Fetch API（connectionId なし）
frontend/static/js/api-client.js  ← connectionId 引数を削除
        ↕
backend/api/v1/metadata.py        ← connection_id クエリパラメータを削除
backend/services/metadata_service.py ← connection_id 引数を削除
backend/connectai/client.py       ← connectionId クエリパラメータを削除
        ↕ HTTPS + RS256 JWT
Connect AI Metadata API  GET /catalogs, /schemas, /tables, /columns
```

---

## 2. バックエンド変更

### 2.1 `backend/connectai/client.py`

各メソッドから `connection_id` 引数と `connectionId` クエリパラメータを削除する。

```python
# 変更前
def get_catalogs(self, connection_id: str) -> list[dict]:
    data = self._get("/catalogs", params={"connectionId": connection_id})

def get_schemas(self, connection_id: str, catalog_name: str) -> list[dict]:
    data = self._get("/schemas", params={
        "connectionId": connection_id,
        "catalogName": catalog_name,
    })

def get_tables(self, connection_id: str, catalog_name: str, schema_name: str) -> list[dict]:
    data = self._get("/tables", params={
        "connectionId": connection_id,
        "catalogName": catalog_name,
        "schemaName": schema_name,
    })

def get_columns(self, connection_id: str, catalog_name: str, schema_name: str, table_name: str) -> list[dict]:
    data = self._get("/columns", params={
        "connectionId": connection_id,
        "catalogName": catalog_name,
        "schemaName": schema_name,
        "tableName": table_name,
    })
```

```python
# 変更後
def get_catalogs(self) -> list[dict]:
    data = self._get("/catalogs")

def get_schemas(self, catalog_name: str) -> list[dict]:
    data = self._get("/schemas", params={"catalogName": catalog_name})

def get_tables(self, catalog_name: str, schema_name: str) -> list[dict]:
    data = self._get("/tables", params={
        "catalogName": catalog_name,
        "schemaName": schema_name,
    })

def get_columns(self, catalog_name: str, schema_name: str, table_name: str) -> list[dict]:
    data = self._get("/columns", params={
        "catalogName": catalog_name,
        "schemaName": schema_name,
        "tableName": table_name,
    })
```

### 2.2 `backend/services/metadata_service.py`

`connection_id` 引数を削除し、client 呼び出しも更新する。

```python
# 変更前
def get_catalogs(self, connection_id: str) -> list[dict]:
    return self._client().get_catalogs(connection_id)

def get_schemas(self, connection_id: str, catalog_name: str) -> list[dict]:
    return self._client().get_schemas(connection_id, catalog_name)

def get_tables(self, connection_id: str, catalog_name: str, schema_name: str) -> list[dict]:
    return self._client().get_tables(connection_id, catalog_name, schema_name)

def get_columns(self, connection_id: str, catalog_name: str, schema_name: str, table_name: str) -> list[dict]:
    return self._client().get_columns(connection_id, catalog_name, schema_name, table_name)
```

```python
# 変更後
def get_catalogs(self) -> list[dict]:
    return self._client().get_catalogs()

def get_schemas(self, catalog_name: str) -> list[dict]:
    return self._client().get_schemas(catalog_name)

def get_tables(self, catalog_name: str, schema_name: str) -> list[dict]:
    return self._client().get_tables(catalog_name, schema_name)

def get_columns(self, catalog_name: str, schema_name: str, table_name: str) -> list[dict]:
    return self._client().get_columns(catalog_name, schema_name, table_name)
```

### 2.3 `backend/api/v1/metadata.py`

`connection_id` クエリパラメータの受け取りとバリデーションを削除する。

```python
# 変更前
@api_v1_bp.route("/api/v1/metadata/catalogs", methods=["GET"])
@login_required
def get_catalogs():
    connection_id = request.args.get("connection_id")
    if not connection_id:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "connection_id は必須です"}}), 400
    catalogs = metadata_service.get_catalogs(connection_id)
    ...

@api_v1_bp.route("/api/v1/metadata/schemas", methods=["GET"])
@login_required
def get_schemas():
    connection_id = request.args.get("connection_id")
    catalog_name = request.args.get("catalog_name")
    if not connection_id or not catalog_name:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "connection_id と catalog_name は必須です"}}), 400
    schemas = metadata_service.get_schemas(connection_id, catalog_name)
    ...
# get_tables, get_columns も同様
```

```python
# 変更後
@api_v1_bp.route("/api/v1/metadata/catalogs", methods=["GET"])
@login_required
def get_catalogs():
    try:
        catalogs = metadata_service.get_catalogs()
    except ConnectAIError as e:
        return jsonify({"error": {"code": "CONNECT_AI_ERROR", "message": str(e)}}), 502
    return jsonify({"catalogs": catalogs}), 200

@api_v1_bp.route("/api/v1/metadata/schemas", methods=["GET"])
@login_required
def get_schemas():
    catalog_name = request.args.get("catalog_name")
    if not catalog_name:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "catalog_name は必須です"}}), 400
    try:
        schemas = metadata_service.get_schemas(catalog_name)
    except ConnectAIError as e:
        return jsonify({"error": {"code": "CONNECT_AI_ERROR", "message": str(e)}}), 502
    return jsonify({"schemas": schemas}), 200

# get_tables: catalog_name / schema_name が必須
# get_columns: catalog_name / schema_name / table_name が必須
```

---

## 3. フロントエンド変更

### 3.1 `frontend/static/js/api-client.js`

各メタデータ取得メソッドから `connectionId` 引数と URL パラメータを削除する。

```javascript
// 変更前
async getCatalogs(connectionId) {
  return this.request('GET', `/metadata/catalogs?connection_id=${encodeURIComponent(connectionId)}`);
}
async getSchemas(connectionId, catalogName) {
  return this.request('GET', `/metadata/schemas?connection_id=${encodeURIComponent(connectionId)}&catalog_name=${encodeURIComponent(catalogName)}`);
}
// getTables, getColumns も同様
```

```javascript
// 変更後
async getCatalogs() {
  return this.request('GET', '/metadata/catalogs');
}
async getSchemas(catalogName) {
  return this.request('GET', `/metadata/schemas?catalog_name=${encodeURIComponent(catalogName)}`);
}
async getTables(catalogName, schemaName) {
  return this.request('GET', `/metadata/tables?catalog_name=${encodeURIComponent(catalogName)}&schema_name=${encodeURIComponent(schemaName)}`);
}
async getColumns(catalogName, schemaName, tableName) {
  return this.request('GET', `/metadata/columns?catalog_name=${encodeURIComponent(catalogName)}&schema_name=${encodeURIComponent(schemaName)}&table_name=${encodeURIComponent(tableName)}`);
}
```

### 3.2 `frontend/pages/explorer.html` / `query.html` / `data-browser.html`

3 画面すべてで同じパターンの変更を適用する。

#### Alpine.js データ変更

```javascript
// 変更前
{
  connections: [],
  selectedConnectionId: '',
  catalogs: [],
  selectedCatalog: '',
  // ...

  async init() {
    const data = await client.getConnections();
    this.connections = data.connections;
    if (this.connections.length > 0) {
      this.selectedConnectionId = this.connections[0].id;
      await this.onConnectionChange();
    }
  },

  async onConnectionChange() {
    // カタログ取得
    const data = await client.getCatalogs(this.selectedConnectionId);
    // ...
  },

  async onCatalogChange() {
    const data = await client.getSchemas(this.selectedConnectionId, this.selectedCatalog);
    // ...
  },
}
```

```javascript
// 変更後
{
  // connections / selectedConnectionId を削除
  catalogs: [],
  selectedCatalog: '',
  // ...

  async init() {
    // 画面初期表示時にカタログ一覧を直接取得
    const data = await client.getCatalogs();
    this.catalogs = data.catalogs;
    if (this.catalogs.length > 0) {
      this.selectedCatalog = this.catalogs[0].TABLE_CATALOG;
      await this.onCatalogChange();
    }
  },

  // onConnectionChange() を削除

  async onCatalogChange() {
    const data = await client.getSchemas(this.selectedCatalog);
    // ...
  },

  async onSchemaChange() {
    const data = await client.getTables(this.selectedCatalog, this.selectedSchema);
    // ...
  },

  async onTableChange() {
    const data = await client.getColumns(this.selectedCatalog, this.selectedSchema, this.selectedTable);
    // ...
  },
}
```

#### UI 変更

コネクション選択ドロップダウンブロック（`explorer.html` 25〜42 行）を削除する。
カタログ選択を常時表示（`x-show="catalogs.length > 0"` は維持）。
初期表示時はカタログ取得中を `loading` で表現する。

---

## 4. テスト変更

### 4.1 `backend/tests/test_metadata.py`

- API 呼び出しから `connection_id=conn-001` クエリパラメータを削除
- `mock_connect_ai_metadata["catalogs"].assert_called_once_with("conn-001")` → `assert_called_once_with()` に変更
- `test_get_catalogs_missing_param`（`connection_id` 未指定で 400）は削除
- `test_get_schemas_missing_param` 等は `catalog_name` 未指定で 400 となる内容に更新

### 4.2 `backend/tests/conftest.py`

`mock_connect_ai_metadata` fixture の mock 設定から `connection_id` 引数を削除する。

---

## 5. 変更ファイル一覧

| ファイル | 変更種別 | 内容 |
|---------|---------|------|
| `backend/connectai/client.py` | 変更 | 各メタデータメソッドから `connection_id` 引数と `connectionId` パラメータを削除 |
| `backend/services/metadata_service.py` | 変更 | 各メソッドから `connection_id` 引数を削除 |
| `backend/api/v1/metadata.py` | 変更 | `connection_id` クエリパラメータの受け取り・バリデーションを削除 |
| `frontend/static/js/api-client.js` | 変更 | 各メタデータメソッドから `connectionId` 引数を削除 |
| `frontend/pages/explorer.html` | 変更 | コネクション選択 UI 削除・`init()` でカタログ直接取得 |
| `frontend/pages/query.html` | 変更 | 同上 |
| `frontend/pages/data-browser.html` | 変更 | 同上 |
| `backend/tests/test_metadata.py` | 変更 | `connection_id` 関連のテストを修正・削除 |
| `backend/tests/conftest.py` | 変更 | `mock_connect_ai_metadata` fixture の引数を修正 |
