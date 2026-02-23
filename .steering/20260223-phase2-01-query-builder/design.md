# 設計書: Phase 2-01 クエリビルダー

**作業ディレクトリ**: `.steering/20260223-phase2-01-query-builder/`
**作成日**: 2026-02-23

---

## 1. 実装方針

Phase 1-03 までの実装パターンを踏襲し、以下の層構造で実装する。

```
frontend/pages/query.html              ← Alpine.js SPA
        ↕ Fetch API
backend/api/v1/query.py               ← Flask エンドポイント
backend/services/query_service.py     ← SQL 組み立て + クエリ実行
backend/connectai/client.py           ← Connect AI HTTP クライアント（拡張）
        ↕ HTTPS + RS256 JWT
Connect AI Query API  POST /query
```

---

## 2. Connect AI Query API 設計

### 2.1 エンドポイント（実装時に curl で検証）

| 操作 | エンドポイント | メソッド |
|------|-------------|---------|
| SQL 実行 | `POST /query` | POST |

**想定リクエストボディ**（Phase 3 実装時に curl で確定する）:
```json
{
  "query": "SELECT [Id], [Name] FROM [Catalog].[Schema].[Table] WHERE [Name] LIKE @p0 LIMIT 1000",
  "parameters": { "@p0": "%John%" },
  "parameterTypes": { "@p0": "VARCHAR" }
}
```

**想定レスポンス**（メタデータ API と同じ形式を想定）:
```json
{
  "results": [{
    "schema": [{"columnName": "Id", ...}, {"columnName": "Name", ...}],
    "rows": [["001", "John Doe"], ["002", "John Smith"]]
  }]
}
```

### 2.2 SQL 構文ルール

Connect AI は SQL-92 ベースで以下を遵守する:

- テーブル参照は完全修飾名 `[Catalog].[Schema].[Table]`
- 識別子（カラム名等）は `[]` でクォート
- パラメータ名は `@` プレフィックス（例：`@p0`）
- ページ上限: `LIMIT 1000`（最大取得行数の保護）
- BETWEEN は `[col] BETWEEN @p0 AND @p1`
- IN は `[col] IN (@p0, @p1, @p2)`

---

## 3. バックエンド設計

### 3.1 ConnectAIClient の変更

**`backend/connectai/client.py`** に以下を追加する。

```python
def query_data(
    self,
    sql: str,
    params: dict | None = None,
    param_types: dict | None = None,
) -> tuple[list[str], list[list]]:
    """
    SQL を実行し、(column_names, rows) を返す。

    Returns:
        (["Id", "Name", ...], [["001", "John"], ...])
    """
    payload: dict = {"query": sql}
    if params:
        payload["parameters"] = params
    if param_types:
        payload["parameterTypes"] = param_types
    data = self._post("/query", payload)
    result = data["results"][0]
    columns = [col["columnName"] for col in result["schema"]]
    rows = result["rows"]
    return columns, rows
```

### 3.2 QuerySchema（新規）

**`backend/schemas/query_schema.py`**

```python
from pydantic import BaseModel

VALID_OPERATORS = {"=", "<>", "<", ">", "<=", ">=", "LIKE", "IN", "BETWEEN"}

class ConditionSchema(BaseModel):
    column: str
    operator: str   # VALID_OPERATORS のいずれか
    value: str
    value2: str = ""  # BETWEEN のみ使用

class QueryRequestSchema(BaseModel):
    connection_id: str
    catalog_name: str
    schema_name: str
    table_name: str
    columns: list[str] = []     # 空 = SELECT *
    conditions: list[ConditionSchema] = []
```

### 3.3 QueryService（新規）

**`backend/services/query_service.py`**

```python
class QueryService:
    def _client(self) -> ConnectAIClient: ...

    def execute_query(self, req: QueryRequestSchema) -> dict:
        """
        クエリを実行し結果を返す。

        Returns:
            {
                "columns": [...],
                "rows": [[...], ...],
                "total": N,
                "elapsed_ms": N,
            }
        """
```

#### SQL 組み立てロジック

```
build_query_sql(catalog, schema, table, columns, conditions)
  → (sql: str, params: dict, param_types: dict)
```

| 演算子 | SQL 断片 | パラメータ |
|--------|---------|----------|
| `=` `<>` `<` `>` `<=` `>=` `LIKE` | `[col] OP @pi` | `@pi = value` |
| `IN` | `[col] IN (@pi_0, @pi_1, ...)` | value をカンマ分割 |
| `BETWEEN` | `[col] BETWEEN @pi_a AND @pi_b` | `@pi_a = value`, `@pi_b = value2` |

全パラメータ型は `VARCHAR` で統一（Connect AI 側で型強制される）。

SELECT 部:
- `columns` が空 → `SELECT *`
- 非空 → `SELECT [col1], [col2], ...`

### 3.4 API エンドポイント（新規）

**`backend/api/v1/query.py`**

| メソッド | パス | 概要 |
|---------|-----|------|
| GET | `/query` | `query.html` レンダリング |
| POST | `/api/v1/query` | クエリ実行 |

```
POST /api/v1/query
Request:  QueryRequestSchema（JSON）
Response: {"columns": [...], "rows": [...], "total": N, "elapsed_ms": N}
Error 400: バリデーションエラー
Error 502: Connect AI エラー
```

---

## 4. テスト設計

### 4.1 Fixture（conftest.py 追加）

**`mock_connect_ai_query`** fixture:

```python
# client.query_data をモック
# 戻り値: (["Id","Name"], [["001","John Doe"],["002","Jane"]])
```

### 4.2 テストケース（`backend/tests/test_query.py`）

| テスト名 | 検証内容 |
|---------|---------|
| `test_execute_query_success` | 200 + columns/rows/total/elapsed_ms |
| `test_execute_query_requires_login` | 未認証で 401 |
| `test_execute_query_missing_param` | 必須パラメータ欠如で 400 |
| `test_execute_query_select_star` | `columns=[]` で SELECT * が呼ばれること |
| `test_execute_query_with_conditions` | WHERE 条件が SQL に反映されること |
| `test_execute_query_connect_ai_error` | Connect AI エラー時に 502 |

### 4.3 SQL 組み立て単体テスト（`test_query.py` 内）

| テスト名 | 検証内容 |
|---------|---------|
| `test_build_sql_no_conditions` | WHERE なし、LIMIT 1000 |
| `test_build_sql_single_condition` | `=` 演算子 + @p0 |
| `test_build_sql_like` | LIKE 演算子 |
| `test_build_sql_in` | IN → 複数パラメータ |
| `test_build_sql_between` | BETWEEN → @p0_a/@p0_b |
| `test_build_sql_select_columns` | 指定カラムのみ SELECT |

---

## 5. フロントエンド設計

### 5.1 APIClient 追加メソッド

**`frontend/static/js/api-client.js`**

```javascript
async executeQuery(connectionId, catalogName, schemaName, tableName, columns, conditions) {
  return this.request('POST', '/query', {
    connection_id: connectionId,
    catalog_name: catalogName,
    schema_name: schemaName,
    table_name: tableName,
    columns,
    conditions,
  });
}
```

### 5.2 query.html のページ構成

```
┌──────────────────────────────────────────────────────────┐
│ ヘッダー: DataHub ロゴ + ダッシュボードリンク + ログアウト  │
├──────────────────────────────────────────────────────────┤
│ [1] データソース選択                                       │
│   コネクション [▼]  カタログ [▼]  スキーマ [▼]  テーブル [▼] │
├──────────────────────────────────────────────────────────┤
│ [2] カラム選択（テーブル選択後に表示）                      │
│   [☑ すべて]  [☑ Id]  [☑ Name]  [☐ Age]  ...            │
├──────────────────────────────────────────────────────────┤
│ [3] WHERE 条件                                           │
│   [Name ▼] [LIKE ▼] [%John%      ] [×]                  │
│   [Age  ▼] [>    ▼] [25          ] [×]                  │
│   （BETWEEN時）[col ▼] [BETWEEN ▼] [20  ] ～ [30  ] [×]  │
│   [+ 条件を追加]                                         │
├──────────────────────────────────────────────────────────┤
│                     [▶ 実行]  [↓ CSV]                   │
├──────────────────────────────────────────────────────────┤
│ [4] 結果: 42 件 | 156ms                                  │
│ ┌──────┬──────────┬──────┐                              │
│ │ Id   │ Name     │ Age  │                              │
│ ├──────┼──────────┼──────┤                              │
│ │ 001  │ John Doe │ 25   │                              │
│ └──────┴──────────┴──────┘                              │
│   [< 前へ]  1 / 3  [次へ >]                              │
└──────────────────────────────────────────────────────────┘
```

### 5.3 Alpine.js データ構造

```javascript
{
  // データソース選択（explorer.html と同じカスケード）
  connections: [],      selectedConnectionId: '',
  catalogs: [],         selectedCatalog: '',
  schemas: [],          selectedSchema: '',
  tables: [],           selectedTable: '',

  // カラム選択
  availableColumns: [], // getColumns の戻り値
  selectedColumns: [],  // 選択中カラム名配列（空 = SELECT *）
  selectAllColumns: true,

  // WHERE 条件
  conditions: [],       // [{id, column, operator, value, value2}]
  operators: ['=', '<>', '<', '>', '<=', '>=', 'LIKE', 'IN', 'BETWEEN'],

  // UI 状態
  loadingMeta: false,
  executing: false,
  error: null,

  // 結果
  resultColumns: [],
  resultRows: [],
  total: 0,
  elapsedMs: 0,
  page: 1,
  pageSize: 20,

  // 計算プロパティ
  get totalPages() { return Math.ceil(this.total / this.pageSize); },
  get pagedRows() {
    const start = (this.page - 1) * this.pageSize;
    return this.resultRows.slice(start, start + this.pageSize);
  },
  get hasResults() { return this.resultColumns.length > 0; },
  get selectedColumnsForRequest() {
    return this.selectAllColumns ? [] : this.selectedColumns;
  },

  // メソッド
  async init() { /* コネクション一覧ロード */ },
  async onConnectionChange() { /* カタログ取得 */ },
  async onCatalogChange()    { /* スキーマ取得 */ },
  async onSchemaChange()     { /* テーブル取得 */ },
  async onTableChange()      { /* カラム取得 → availableColumns */ },
  toggleSelectAll()          { /* すべて切り替え */ },
  toggleColumn(name)         { /* 個別カラム切り替え */ },
  addCondition()             { /* 空行追加 */ },
  removeCondition(id)        { /* 行削除 */ },
  async executeQuery()       { /* POST /api/v1/query → resultRows */ },
  downloadCSV()              { /* Blob ダウンロード */ },
}
```

### 5.4 CSV ダウンロード実装

```javascript
downloadCSV() {
  const header = this.resultColumns.join(',');
  const body = this.resultRows.map(row =>
    row.map(v => `"${String(v ?? '').replace(/"/g, '""')}"`).join(',')
  ).join('\n');
  const blob = new Blob([header + '\n' + body], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${this.selectedTable}_${new Date().toISOString().slice(0,10).replace(/-/g,'')}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}
```

### 5.5 ダッシュボードへのリンク追加

**`frontend/pages/dashboard.html`** の「データ管理」セクションにクエリビルダーへのリンクを追加する。

---

## 6. 変更ファイル一覧

| ファイル | 変更種別 | 内容 |
|---------|---------|------|
| `backend/connectai/client.py` | 変更 | `query_data()` メソッド追加 |
| `backend/schemas/query_schema.py` | 新規 | `QueryRequestSchema`, `ConditionSchema` |
| `backend/services/query_service.py` | 新規 | `QueryService`, `build_query_sql()` |
| `backend/api/v1/query.py` | 新規 | ページルート + `POST /api/v1/query` |
| `backend/api/v1/__init__.py` | 変更 | `from . import query` 追加 |
| `backend/tests/conftest.py` | 変更 | `mock_connect_ai_query` fixture 追加 |
| `backend/tests/test_query.py` | 新規 | 12テストケース |
| `frontend/pages/query.html` | 新規 | クエリビルダー画面 |
| `frontend/static/js/api-client.js` | 変更 | `executeQuery()` メソッド追加 |
| `frontend/pages/dashboard.html` | 変更 | クエリビルダーへのリンク追加 |
