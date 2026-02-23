# 設計書: Phase 2-02 データ CRUD 操作

**作業ディレクトリ**: `.steering/20260223-phase2-02-crud/`
**作成日**: 2026-02-23

---

## 1. 実装方針

既存の Phase 2-01（クエリビルダー）の層構造を踏襲し、新しいファイル群として追加する。
`ConnectAIClient.query_data()` は INSERT / UPDATE / DELETE SQL も実行できるため、
クライアントの拡張は不要（既存メソッドを DML にも流用する）。

```
frontend/pages/data-browser.html        ← Alpine.js SPA
        ↕ Fetch API
backend/api/v1/data.py                  ← Flask エンドポイント（新規）
backend/services/data_service.py        ← SQL 組み立て + 実行（新規）
backend/schemas/data_schema.py          ← Pydantic バリデーション（新規）
backend/connectai/client.py             ← 変更あり（DML レスポンス対応・エラーメッセージ改善）
        ↕ HTTPS + RS256 JWT
Connect AI SQL API  POST /query
```

---

## 2. Connect AI SQL API との接続

### 2.1 SQL 構文ルール（既存ルールを継承）

| 規則 | 例 |
|-----|---|
| 識別子を `[]` でクォート | `[Catalog].[Schema].[Table]`、`[ColumnName]` |
| パラメータは `@` プレフィックス | `@s0`, `@w0` |
| 全値を VARCHAR で送信 | Connect AI 側で型強制される |

### 2.2 DML 実行の仕組み

既存の `ConnectAIClient.query_data(sql, params, param_types)` に INSERT / UPDATE / DELETE を渡すと、
Connect AI は `{"affectedRows": N, "rowsTruncated": false}` のみを返す（`schema` / `rows` キーは含まれない）。

```python
# DML 成功時の実際のレスポンス例
{
  "results": [{"affectedRows": 1, "rowsTruncated": false}]
}
```

`query_data()` 内では `"schema"` キーの有無でレスポンス種別を判定し、
DML レスポンスの場合は `([], [])` を返す（呼び出し元は戻り値を使用しないため問題なし）。

```python
# query_data() でのレスポンス判定
result = data["results"][0]
if "schema" not in result:
    return [], []   # DML 成功
columns = [col["columnName"] for col in result["schema"]]
rows = result["rows"]
return columns, rows
```

また、`query_data()` はエラー時に SQL と送信パラメータをエラーメッセージに付与することで、
デバッグを容易にしている：

```python
sql_context = f" | [Sent] SQL: {sql} | Parameters: {json.dumps(params, ...)}"
try:
    data = self._post("/query", payload)
except ConnectAIError as e:
    raise ConnectAIError(f"{e}{sql_context}") from e
```

---

## 3. バックエンド設計

### 3.1 Pydantic スキーマ（新規）

**`backend/schemas/data_schema.py`**

```python
from pydantic import BaseModel

class RecordListSchema(BaseModel):
    connection_id: str
    catalog: str
    schema_name: str   # 'schema' は Python 予約語と衝突しないが Pydantic 推奨の命名で回避
    table: str
    limit: int = 20
    offset: int = 0

class RecordWriteSchema(BaseModel):
    """INSERT / UPDATE 共通：書き込みデータ"""
    connection_id: str
    catalog: str
    schema_name: str
    table: str
    data: dict[str, str]   # {カラム名: 値} ※全値を文字列で受け取り Connect AI に委ねる

class RecordUpdateSchema(RecordWriteSchema):
    """UPDATE 用：WHERE 条件を追加"""
    where: dict[str, str]  # {カラム名: 値}

class RecordDeleteSchema(BaseModel):
    """DELETE 用"""
    connection_id: str
    catalog: str
    schema_name: str
    table: str
    where: dict[str, str]
```

### 3.2 SQL 組み立て関数（新規）

**`backend/services/data_service.py`** に純粋関数として定義。
テストが容易になるようサービスクラスから切り出す。

#### `build_select_sql(catalog, schema, table, limit, offset)`

```sql
SELECT * FROM [catalog].[schema].[table] LIMIT {limit} OFFSET {offset}
```

- パラメータなし（LIMIT / OFFSET は整数として直接埋め込み）
- limit は 1〜100 に clamp する

#### `build_count_sql(catalog, schema, table)`

```sql
SELECT COUNT(*) AS [cnt] FROM [catalog].[schema].[table]
```

- パラメータなし

#### `build_insert_sql(catalog, schema, table, data)`

```python
# data = {"Name": "Acme", "Industry": "Tech"}
sql   = "INSERT INTO [cat].[sch].[tbl] ([Name], [Industry]) VALUES (@s0, @s1)"
params = {"@s0": "Acme", "@s1": "Tech"}
param_types = {"@s0": "VARCHAR", "@s1": "VARCHAR"}
```

- カラム名インデックスで `@s0`, `@s1`, ... と命名（特殊文字を回避）

#### `build_update_sql(catalog, schema, table, data, where)`

```python
# data  = {"Name": "Acme Corp"}
# where = {"Id": "001xxx"}
sql = "UPDATE [cat].[sch].[tbl] SET [Name] = @s0 WHERE [Id] = @w0"
params = {"@s0": "Acme Corp", "@w0": "001xxx"}
param_types = {"@s0": "VARCHAR", "@w0": "VARCHAR"}
```

- SET: `@s0`, `@s1`, ...
- WHERE: `@w0`, `@w1`, ...
- 名前空間を分けて衝突を防ぐ

#### `build_delete_sql(catalog, schema, table, where)`

```python
# where = {"Id": "001xxx"}
sql = "DELETE FROM [cat].[sch].[tbl] WHERE [Id] = @w0"
params = {"@w0": "001xxx"}
param_types = {"@w0": "VARCHAR"}
```

### 3.3 DataService クラス（新規）

**`backend/services/data_service.py`**

```python
class DataService:

    def _client(self) -> ConnectAIClient:
        return ConnectAIClient(child_account_id=current_user.connect_ai_account_id)

    def list_records(self, req: RecordListSchema) -> dict:
        """
        レコード一覧 + 総件数を返す。
        Returns:
            {"columns": [...], "rows": [...], "total": N, "limit": N, "offset": N}
        """

    def create_record(self, req: RecordWriteSchema) -> dict:
        """
        INSERT を実行して成功メッセージを返す。
        Returns:
            {"message": "Record created successfully."}
        """

    def update_record(self, req: RecordUpdateSchema) -> dict:
        """
        UPDATE を実行して成功メッセージを返す。
        """

    def delete_record(self, req: RecordDeleteSchema) -> dict:
        """
        DELETE を実行して成功メッセージを返す。
        """
```

#### 総件数取得の実装方針

`COUNT(*)` が Connect AI でサポートされない場合を考慮し、
`list_records` では以下の順で試みる：

1. `build_count_sql` を実行して `rows[0][0]` を total として使用
2. `ConnectAIError` が発生した場合は total を `-1`（不明）として返す
   （UI 上は「全 N 件」表示を省略し「20 件取得」のみ表示する）

### 3.4 API エンドポイント（新規）

**`backend/api/v1/data.py`**

| メソッド | パス | 処理 |
|---------|-----|------|
| GET | `/data-browser` | `data-browser.html` レンダリング |
| GET | `/api/v1/data/records` | レコード一覧取得 |
| POST | `/api/v1/data/records` | レコード作成 |
| PUT | `/api/v1/data/records` | レコード更新 |
| DELETE | `/api/v1/data/records` | レコード削除 |

```
GET /api/v1/data/records?connection_id=...&catalog=...&schema_name=...&table=...&limit=20&offset=0
→ 200: {"columns": [...], "rows": [...], "total": N, "limit": 20, "offset": 0}
→ 400: バリデーションエラー
→ 401: 未認証
→ 502: Connect AI エラー

POST /api/v1/data/records  Body: RecordWriteSchema
→ 201: {"message": "Record created successfully."}
→ 400: バリデーションエラー
→ 401: 未認証
→ 502: Connect AI エラー

PUT /api/v1/data/records   Body: RecordUpdateSchema
→ 200: {"message": "Record updated successfully."}
→ 400: バリデーションエラー（where が空の場合を含む）
→ 401: 未認証
→ 502: Connect AI エラー

DELETE /api/v1/data/records  Body: RecordDeleteSchema
→ 200: {"message": "Record deleted successfully."}
→ 400: バリデーションエラー（where が空の場合を含む）
→ 401: 未認証
→ 502: Connect AI エラー
```

**バリデーション追加ルール**:
- `RecordUpdateSchema.where` が空 dict の場合 → 400 を返す（全件 UPDATE を防止）
- `RecordDeleteSchema.where` が空 dict の場合 → 400 を返す（全件 DELETE を防止）

---

## 4. テスト設計

### 4.1 Fixture（`conftest.py` 追加）

```python
@pytest.fixture
def mock_connect_ai_crud():
    """Connect AI クエリ API（SELECT / DML 両用）をモックする"""
    with patch("backend.connectai.client.ConnectAIClient.query_data") as mock:
        # SELECT 用デフォルト戻り値
        mock.return_value = (
            ["Id", "Name", "Industry"],
            [
                ["001", "Acme Corp", "Technology"],
                ["002", "Widget Co", "Manufacturing"],
            ],
        )
        yield mock
```

### 4.2 テストケース（`backend/tests/test_data.py`）

#### API テスト（9 件）

| テスト名 | 検証内容 |
|---------|---------|
| `test_get_records_success` | 200 + columns / rows / total |
| `test_get_records_requires_login` | 未認証で 401 |
| `test_get_records_missing_param` | 必須パラメータ欠如で 400 |
| `test_create_record_success` | 201 + message |
| `test_create_record_requires_login` | 未認証で 401 |
| `test_update_record_success` | 200 + message |
| `test_update_record_requires_login` | 未認証で 401 |
| `test_delete_record_success` | 200 + message |
| `test_delete_record_requires_login` | 未認証で 401 |

#### SQL 組み立て単体テスト（5 件）

| テスト名 | 検証内容 |
|---------|---------|
| `test_build_select_sql` | `SELECT *` + `LIMIT 20 OFFSET 0` |
| `test_build_count_sql` | `SELECT COUNT(*) AS [cnt]` |
| `test_build_insert_sql` | `INSERT INTO ... VALUES (@s0, @s1)` + params |
| `test_build_update_sql` | `SET [col] = @s0 WHERE [col] = @w0` + params |
| `test_build_delete_sql` | `DELETE FROM ... WHERE [col] = @w0` + params |

---

## 5. フロントエンド設計

### 5.1 APIClient 追加メソッド

**`frontend/static/js/api-client.js`** に追加：

```javascript
async getRecords(connectionId, catalog, schemaName, table, limit = 20, offset = 0) {
  const params = new URLSearchParams({ connection_id: connectionId, catalog, schema_name: schemaName, table, limit, offset });
  return this.request('GET', `/data/records?${params}`);
}

async createRecord(connectionId, catalog, schemaName, table, data) {
  return this.request('POST', '/data/records', { connection_id: connectionId, catalog, schema_name: schemaName, table, data });
}

async updateRecord(connectionId, catalog, schemaName, table, data, where) {
  return this.request('PUT', '/data/records', { connection_id: connectionId, catalog, schema_name: schemaName, table, data, where });
}

async deleteRecord(connectionId, catalog, schemaName, table, where) {
  return this.request('DELETE', '/data/records', { connection_id: connectionId, catalog, schema_name: schemaName, table, where });
}
```

### 5.2 data-browser.html のページ構成

```
┌──────────────────────────────────────────────────────────────┐
│ ヘッダー: DataHub ロゴ + ナビ + ログアウト                      │
├──────────────────────────────────────────────────────────────┤
│ [1] データソース選択（ページ表示時に先頭要素を自動選択）          │
│  コネクション [▼]  カタログ [▼]  スキーマ [▼]  テーブル [▼]    │
│                                                              │
│  キー列（WHERE 条件に使用）: [Id ▼]   [+ 新規レコード追加]      │
├──────────────────────────────────────────────────────────────┤
│ [2] レコード一覧テーブル（操作列は左端）                         │
│  ┌──────────┬───────┬──────────────┬─────────────┐          │
│  │ 操作      │ Id    │ Name         │ Industry    │          │
│  ├──────────┼───────┼──────────────┼─────────────┤          │
│  │[編集][削除]│ 001   │ Acme Corp    │ Technology  │          │
│  │[編集][削除]│ 002   │ Widget Co    │ Manufacture │          │
│  └──────────┴───────┴──────────────┴─────────────┘          │
├──────────────────────────────────────────────────────────────┤
│ [3] ページネーション                                            │
│   1〜20 件目 / 全 150 件   [< 前へ]  [次へ >]                  │
└──────────────────────────────────────────────────────────────┘

[モーダル: レコード作成・編集フォーム]
┌──────────────────────────────────────┐
│ 新規レコード / レコード編集           │
│ Id       [001xxx          ]          │
│ Name     [Acme Corp       ]          │
│ Industry [Technology      ]          │
│                  [キャンセル] [保存]  │
└──────────────────────────────────────┘

[インライン: 削除確認]
「"Acme Corp" を削除しますか？」 [キャンセル] [削除する]
```

### 5.3 Alpine.js データ構造

```javascript
{
  // データソース選択（query.html と同じカスケード）
  connections: [],      selectedConnectionId: '',
  catalogs: [],         selectedCatalog: '',
  schemas: [],          selectedSchema: '',
  tables: [],           selectedTable: '',
  columns: [],          // getColumns の結果（カラムメタ情報）
  keyColumn: '',        // WHERE に使うカラム名（デフォルト: 最初のカラム）

  // レコード一覧
  recordColumns: [],    // ["Id", "Name", ...]
  recordRows: [],       // [["001", "Acme", ...], ...]
  total: 0,
  limit: 20,
  offset: 0,

  // UI 状態
  loading: false,
  error: null,
  successMessage: null,

  // モーダル
  showModal: false,
  modalMode: 'create',  // 'create' | 'edit'
  editingRow: null,     // 元の行データ {col: val}
  formData: {},         // {col: val}

  // 削除確認
  confirmingRow: null,  // 削除確認中の行データ

  // 計算プロパティ
  get currentPage() { return Math.floor(this.offset / this.limit) + 1; },
  get hasNext() { return this.total < 0 || this.offset + this.limit < this.total; },
  get hasPrev() { return this.offset > 0; },
  get rangeLabel() {
    if (this.total < 0) return `${this.offset + 1}〜${this.offset + this.recordRows.length} 件`;
    return `${this.offset + 1}〜${this.offset + this.recordRows.length} 件目 / 全 ${this.total} 件`;
  },

  // 初期化
  async init() { /* コネクション一覧ロード */ },

  // カスケード選択
  async onConnectionChange() { /* カタログ取得 */ },
  async onCatalogChange()    { /* スキーマ取得 */ },
  async onSchemaChange()     { /* テーブル取得 */ },
  async onTableChange()      { /* カラム取得 → keyColumn = columns[0] → loadRecords() */ },

  // CRUD 操作
  async loadRecords()        { /* GET /api/v1/data/records */ },
  openCreateModal()          { /* formData = {} → showModal = true, mode = create */ },
  openEditModal(row)         { /* editingRow = row, formData = {...row} → showModal = true, mode = edit */ },
  async saveRecord()         { /* modalMode に応じて POST or PUT → closeModal → loadRecords */ },
  confirmDelete(row)         { /* confirmingRow = row */ },
  cancelDelete()             { /* confirmingRow = null */ },
  async deleteRecord()       { /* DELETE → confirmingRow = null → loadRecords */ },

  // ページネーション
  nextPage()                 { this.offset += this.limit; this.loadRecords(); },
  prevPage()                 { this.offset -= this.limit; this.loadRecords(); },

  // フォーム自動生成ヘルパー
  inputType(column) {
    // column.TYPE_NAME に応じて input type を返す
    // 'INTEGER' | 'BIGINT' → 'number'
    // 'BOOLEAN' → 'checkbox'
    // 'DATE' → 'date'
    // 'TIMESTAMP' → 'datetime-local'
    // その他 → 'text'
  },
  isRequired(column) { return !column.IS_NULLABLE; },

  // WHERE 条件の生成
  whereForRow(row) {
    // {keyColumn: row[keyColumn のインデックス]} を返す
    const idx = this.recordColumns.indexOf(this.keyColumn);
    return { [this.keyColumn]: row[idx] };
  },
}
```

### 5.4 フォームの動的生成ロジック

```html
<!-- Alpine.js テンプレート -->
<template x-for="col in columns" :key="col.COLUMN_NAME">
  <div class="form-group">
    <label x-text="col.COLUMN_NAME"></label>
    <span x-show="isRequired(col)" class="text-red-500">*</span>

    <!-- checkbox -->
    <input x-show="inputType(col) === 'checkbox'"
           type="checkbox"
           :checked="formData[col.COLUMN_NAME] === 'true'"
           @change="formData[col.COLUMN_NAME] = $event.target.checked ? 'true' : 'false'" />

    <!-- その他 -->
    <input x-show="inputType(col) !== 'checkbox'"
           :type="inputType(col)"
           :required="isRequired(col)"
           x-model="formData[col.COLUMN_NAME]" />
  </div>
</template>
```

### 5.5 ダッシュボードへのリンク追加

**`frontend/pages/dashboard.html`** のナビゲーションに「データブラウザ」カードを追加する。

---

## 6. 変更ファイル一覧

| ファイル | 変更種別 | 内容 |
|---------|---------|------|
| `backend/schemas/data_schema.py` | **新規** | `RecordListSchema`, `RecordWriteSchema`, `RecordUpdateSchema`, `RecordDeleteSchema` |
| `backend/services/data_service.py` | **新規** | SQL 組み立て関数 + `DataService` クラス |
| `backend/api/v1/data.py` | **新規** | ページルート + CRUD API 4 本 |
| `backend/api/v1/__init__.py` | 変更 | `from . import data` 追加 |
| `backend/api/v1/auth.py` | 変更 | ルート URL `/` → `/dashboard` リダイレクト追加 |
| `backend/connectai/client.py` | 変更 | DML レスポンス対応（`schema` キー有無で判定）・エラーメッセージに SQL コンテキスト付与 |
| `backend/tests/conftest.py` | 変更 | `mock_connect_ai_crud` fixture 追加 |
| `backend/tests/test_data.py` | **新規** | 14 テストケース |
| `frontend/pages/data-browser.html` | **新規** | データブラウザ画面（操作列は左端・初期自動選択） |
| `frontend/static/js/api-client.js` | 変更 | `getRecords`, `createRecord`, `updateRecord`, `deleteRecord` 追加 |
| `frontend/pages/dashboard.html` | 変更 | データブラウザへのリンク追加 |
| `.vscode/launch.json` | **新規** | VS Code デバッグ構成（Flask 起動・pytest） |
| `.vscode/settings.json` | **新規** | VS Code ワークスペース設定（Python インタープリター・pytest） |

---

## 7. 実装上の注意事項

### 7.1 全件 UPDATE / DELETE の防止

`where` が空の場合は `DataService` 側でも明示的に `ValueError` を raise し、
エンドポイントが 400 を返すようにする（スキーマバリデーションだけに依存しない二重保護）。

### 7.2 NULL 値の扱い

Connect AI の SQL パラメータは全て文字列として送信する。
NULL を表現したい場合、ユーザーが入力欄を空にした場合は値を空文字列 `""` として送信する。
（NULL vs 空文字の区別は Connect AI 側の型強制に依存する）

### 7.3 `schema_name` の命名

Python の `BaseModel` で `schema` フィールド名は Pydantic 内部と衝突するリスクがあるため、
`schema_name` を使用する。フロントエンドとの通信でも `schema_name` キーを統一する。
