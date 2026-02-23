# 設計書: Phase 1-03 メタデータエクスプローラー

**作業ディレクトリ**: `.steering/20260223-phase1-03-metadata-explorer/`
**作成日**: 2026-02-23

---

## 1. 実装方針

Phase 1-02 までの実装パターンを踏襲し、以下の層構造で実装する。

```
frontend/pages/explorer.html          ← Alpine.js SPA
        ↕ Fetch API
backend/api/v1/metadata.py            ← Flask エンドポイント
backend/services/metadata_service.py  ← ビジネスロジック
backend/connectai/client.py           ← Connect AI HTTP クライアント（既存・拡張）
        ↕ HTTPS + RS256 JWT
Connect AI Powered-By Metadata API
```

---

## 2. Connect AI API 設計

### 2.1 エンドポイント（実装時に curl で検証）

| 操作 | 想定エンドポイント | クエリパラメータ |
|------|-----------------|----------------|
| カタログ一覧 | `GET /poweredby/catalogs` | `connectionId` |
| スキーマ一覧 | `GET /poweredby/schemas` | `connectionId`, `catalogName` |
| テーブル一覧 | `GET /poweredby/tables` | `connectionId`, `catalogName`, `schemaName` |
| カラム一覧 | `GET /poweredby/columns` | `connectionId`, `catalogName`, `schemaName`, `tableName` |

**注**: 実際のパス・パラメータ名は実装フェーズ（フェーズ3）の最初に curl で検証する。
`/catalogs` 等の短いパスの可能性もある。

### 2.2 JWT の `sub` クレーム

メタデータ取得はユーザーの子アカウントに紐づくコネクションを使用するため、
`sub = current_user.connect_ai_account_id` を使用する（`sub=""` は使わない）。

### 2.3 connectionId

Connect AI が発行するコネクションの ID（`GET /poweredby/connection/list` の `id` フィールド）を使用する。

---

## 3. バックエンド設計

### 3.1 ConnectAIClient の変更

**`backend/connectai/client.py`** に以下を追加・変更する。

#### `_get()` の拡張

クエリパラメータを渡せるよう `params` 引数を追加する。

```python
def _get(self, path: str, params: dict | None = None) -> dict:
    url = f"{self.base_url}{path}"
    try:
        resp = requests.get(url, headers=self._headers(), params=params, timeout=30)
        ...
```

#### 新規メソッド

```python
def get_catalogs(self, connection_id: str) -> list[dict]:
    """カタログ一覧を返す。"""
    data = self._get("/poweredby/catalogs", params={"connectionId": connection_id})
    # レスポンスキーは実装時に検証して確定する

def get_schemas(self, connection_id: str, catalog_name: str) -> list[dict]:
    """スキーマ一覧を返す。"""
    data = self._get("/poweredby/schemas", params={
        "connectionId": connection_id,
        "catalogName": catalog_name,
    })

def get_tables(self, connection_id: str, catalog_name: str, schema_name: str) -> list[dict]:
    """テーブル一覧を返す。"""
    data = self._get("/poweredby/tables", params={
        "connectionId": connection_id,
        "catalogName": catalog_name,
        "schemaName": schema_name,
    })

def get_columns(self, connection_id: str, catalog_name: str, schema_name: str, table_name: str) -> list[dict]:
    """カラム一覧を返す。"""
    data = self._get("/poweredby/columns", params={
        "connectionId": connection_id,
        "catalogName": catalog_name,
        "schemaName": schema_name,
        "tableName": table_name,
    })
```

### 3.2 MetadataService（新規）

**`backend/services/metadata_service.py`**

```python
class MetadataService:
    def _client(self) -> ConnectAIClient:
        return ConnectAIClient(child_account_id=current_user.connect_ai_account_id)

    def get_catalogs(self, connection_id: str) -> list[dict]: ...
    def get_schemas(self, connection_id: str, catalog_name: str) -> list[dict]: ...
    def get_tables(self, connection_id: str, catalog_name: str, schema_name: str) -> list[dict]: ...
    def get_columns(self, connection_id: str, catalog_name: str, schema_name: str, table_name: str) -> list[dict]: ...
```

### 3.3 API エンドポイント（新規）

**`backend/api/v1/metadata.py`**

| メソッド | パス | クエリパラメータ | レスポンス |
|---------|-----|----------------|----------|
| GET | `/explorer` | - | `explorer.html` レンダリング |
| GET | `/api/v1/metadata/catalogs` | `connection_id` | `{"catalogs": [...]}` |
| GET | `/api/v1/metadata/schemas` | `connection_id`, `catalog_name` | `{"schemas": [...]}` |
| GET | `/api/v1/metadata/tables` | `connection_id`, `catalog_name`, `schema_name` | `{"tables": [...]}` |
| GET | `/api/v1/metadata/columns` | `connection_id`, `catalog_name`, `schema_name`, `table_name` | `{"columns": [...]}` |

すべてのエンドポイントに `@login_required` を付与する。

必須パラメータ欠如時は 400 を返す。

エラーレスポンス形式は既存 API と統一：
```json
{ "error": { "code": "...", "message": "..." } }
```

### 3.4 `__init__.py` の更新

`backend/api/v1/__init__.py` に `from . import metadata` を追加する。

---

## 4. テスト設計

**`backend/tests/test_metadata.py`**

### 4.1 Fixture

`conftest.py` に `mock_connect_ai_metadata` fixture を追加する：
- `get_catalogs` → `[{"catalogName": "Salesforce1"}, ...]`
- `get_schemas` → `[{"schemaName": "dbo"}, ...]`
- `get_tables` → `[{"tableName": "Account"}, {"tableName": "Contact"}, ...]`
- `get_columns` → `[{"columnName": "Id", "dataType": "VARCHAR", "isNullable": "NO"}, ...]`

### 4.2 テストケース（9件）

| テスト名 | 検証内容 |
|---------|---------|
| `test_get_catalogs_success` | 200 + `{"catalogs": [...]}` |
| `test_get_catalogs_requires_login` | 未認証で 401 |
| `test_get_schemas_success` | 200 + `{"schemas": [...]}` |
| `test_get_schemas_requires_login` | 未認証で 401 |
| `test_get_tables_success` | 200 + `{"tables": [...]}` |
| `test_get_tables_requires_login` | 未認証で 401 |
| `test_get_columns_success` | 200 + `{"columns": [...]}` |
| `test_get_columns_requires_login` | 未認証で 401 |
| `test_get_catalogs_missing_param` | `connection_id` 欠如で 400 |

---

## 5. フロントエンド設計

### 5.1 APIClient 追加メソッド

**`frontend/static/js/api-client.js`**

```javascript
async getCatalogs(connectionId) {
  return this.request('GET', `/metadata/catalogs?connection_id=${encodeURIComponent(connectionId)}`);
}
async getSchemas(connectionId, catalogName) {
  return this.request('GET', `/metadata/schemas?connection_id=...&catalog_name=...`);
}
async getTables(connectionId, catalogName, schemaName) { ... }
async getColumns(connectionId, catalogName, schemaName, tableName) { ... }
```

### 5.2 explorer.html のページ構成

```
┌─────────────────────────────────────────────────────┐
│  Header: DataHub ロゴ + ログアウト                   │
├─────────────────────────────────────────────────────┤
│  コネクション選択: [セレクトボックス ▼]               │
├─────────────────────────────────────────────────────┤
│  ブレッドクラム: MyConnection > Catalog1 > dbo >     │
├─────────────────────────────────────────────────────┤
│  コンテンツ                                          │
│                                                     │
│  [catalogs表示時]                                   │
│  ┌──────────────────┐ ┌──────────────────┐          │
│  │ 📁 Salesforce1   │ │ 📁 Catalog2       │          │
│  └──────────────────┘ └──────────────────┘          │
│                                                     │
│  [tables表示時]                                     │
│  フィルタ: [____________________]                   │
│  ┌──────────────┐ ┌──────────────┐ ...             │
│  │ 📋 Account   │ │ 📋 Contact   │                  │
│  └──────────────┘ └──────────────┘                  │
│                                                     │
│  [columns表示時]                                    │
│  テーブル: Account                                  │
│  ┌──────────┬────────────┬───────────┐              │
│  │ カラム名 │ データ型   │ NULL 可否 │              │
│  ├──────────┼────────────┼───────────┤              │
│  │ Id       │ VARCHAR    │ NO        │              │
│  │ Name     │ VARCHAR    │ YES       │              │
│  └──────────┴────────────┴───────────┘              │
└─────────────────────────────────────────────────────┘
```

### 5.3 Alpine.js データ構造

```javascript
{
  // 初期化
  connections: [],         // GET /api/v1/connections
  selectedConnectionId: '',
  selectedConnectionName: '',

  // ドリルダウン状態
  // level: 'init' | 'catalogs' | 'schemas' | 'tables' | 'columns'
  level: 'init',
  catalogs: [],
  selectedCatalog: '',
  schemas: [],
  selectedSchema: '',
  tables: [],
  tableFilter: '',
  columns: [],
  selectedTable: '',

  // UI 状態
  loading: false,
  error: null,

  // 計算プロパティ（x-data 内の getter）
  get filteredTables() {
    return this.tables.filter(t => t.tableName.toLowerCase().includes(this.tableFilter.toLowerCase()));
  },

  // メソッド
  async init() { /* コネクション一覧ロード */ },
  async onConnectionChange() { /* カタログ取得 → level = 'catalogs' */ },
  async selectCatalog(catalogName) { /* スキーマ取得 → level = 'schemas' */ },
  async selectSchema(schemaName) { /* テーブル取得 → level = 'tables' */ },
  async selectTable(tableName) { /* カラム取得 → level = 'columns' */ },
  navigateTo(targetLevel) { /* ブレッドクラムからの戻り処理 */ },
}
```

### 5.4 ダッシュボードへのリンク追加

**`frontend/pages/dashboard.html`** の「データ管理」セクションにエクスプローラーへのリンクを追加する。

---

## 6. 変更ファイル一覧

| ファイル | 変更種別 | 内容 |
|---------|---------|------|
| `backend/connectai/client.py` | 変更 | `_get()` に `params` 追加、メタデータ4メソッド追加 |
| `backend/services/metadata_service.py` | 新規 | `MetadataService` クラス |
| `backend/api/v1/metadata.py` | 新規 | ページルート + 4 API エンドポイント |
| `backend/api/v1/__init__.py` | 変更 | `from . import metadata` 追加 |
| `backend/tests/conftest.py` | 変更 | `mock_connect_ai_metadata` fixture 追加 |
| `backend/tests/test_metadata.py` | 新規 | 9テストケース |
| `frontend/static/js/api-client.js` | 変更 | メタデータ4メソッド追加 |
| `frontend/pages/explorer.html` | 新規 | メタデータエクスプローラー画面 |
| `frontend/pages/dashboard.html` | 変更 | エクスプローラーへのリンク追加 |
