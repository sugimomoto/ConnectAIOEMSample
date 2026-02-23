# SQL API

## 概要

SQL APIは、データソースに対してSQLクエリを実行するための機能を提供します。

## 主要機能

SQL APIは以下の3つの主要な操作を提供しています：

1. **Query Operation** - 単一のSQLクエリを実行
2. **Batch Operation** - バッチでINSERT、UPDATE、DELETEを実行
3. **Execute Procedure** - ストアドプロシージャを実行

---

## 1. Query Operation（クエリ実行）

データソースに対してSQLクエリを実行します。

### エンドポイント

```http
POST /query
```

### リクエスト

**ヘッダー：**
```http
Authorization: Bearer {JWT_TOKEN}
Content-Type: application/json
```

**パラメータ：**

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `query` | string | ○ | 実行するSQLクエリ（SELECT、INSERT、UPDATE、DELETE、EXEC） |
| `defaultCatalog` | string | × | デフォルトのカタログ名 |
| `defaultSchema` | string | × | デフォルトのスキーマ名 |
| `parameters` | object | × | パラメータ化クエリの値 |
| `schemaOnly` | boolean | × | スキーマのみを返す（デフォルト: false） |
| `timeout` | integer | × | タイムアウト秒数（1～300秒） |

**リクエスト例：**

```json
{
  "query": "SELECT [FirstName], [LastName] FROM [Customers] WHERE [CustomerId] = @CustomerId",
  "defaultCatalog": "Salesforce1",
  "parameters": {
    "CustomerId": {
      "dataType": 5,
      "value": "12345"
    }
  },
  "timeout": 60
}
```

### パラメータ化クエリ

`parameters`オブジェクトで各パラメータを以下の形式で指定します：

```json
{
  "parameterName": {
    "dataType": <1～18の整数値>,
    "value": <パラメータの値>
  }
}
```

**データ型の値：**
- 5: VARCHAR
- 3: INTEGER
- その他のデータ型については[REST API基本仕様](./rest-api-basics.md#サポートされるデータ型)を参照

### レスポンス

**ステータス：** 200 OK

```json
{
  "results": [{
    "affectedRows": -1,
    "schema": [{
      "catalogName": "Salesforce1",
      "columnLabel": "FirstName",
      "columnName": "FirstName",
      "dataType": 5,
      "dataTypeName": "VARCHAR"
    }],
    "rows": [
      ["John", "Doe"],
      ["Jane", "Smith"]
    ]
  }],
  "error": null
}
```

---

## 2. Batch Operation（バッチ操作）

単一リクエストでINSERT、UPDATE、DELETEをバッチ実行します。

### エンドポイント

```http
POST /batch
```

### リクエスト

**ヘッダー：**
```http
Authorization: Bearer {JWT_TOKEN}
Content-Type: application/json
```

**パラメータ：**

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `query` | string | ○ | 実行するバッチSQLクエリ（INSERT、UPDATE、DELETE） |
| `defaultCatalog` | string | × | デフォルトのカタログ名 |
| `defaultSchema` | string | × | デフォルトのスキーマ名 |
| `parameters` | array | × | パラメータオブジェクトの配列 |
| `timeout` | integer | × | タイムアウト秒数（1～300秒） |

**リクエスト例：**

```json
{
  "query": "INSERT INTO [Customers] ([FirstName], [LastName]) VALUES (@FirstName, @LastName)",
  "defaultCatalog": "Salesforce1",
  "parameters": [
    {
      "FirstName": {"dataType": 5, "value": "John"},
      "LastName": {"dataType": 5, "value": "Doe"}
    },
    {
      "FirstName": {"dataType": 5, "value": "Jane"},
      "LastName": {"dataType": 5, "value": "Smith"}
    }
  ]
}
```

### レスポンス

**ステータス：** 200 OK

```json
{
  "results": [{
    "affectedRows": 2,
    "schema": [],
    "rows": []
  }],
  "error": null
}
```

---

## 3. Execute Procedure（プロシージャ実行）

ストアドプロシージャを実行します。

### エンドポイント

```http
POST /exec
```

### リクエスト

**ヘッダー：**
```http
Authorization: Bearer {JWT_TOKEN}
Content-Type: application/json
```

**パラメータ：**

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `procedure` | string | ○ | 実行するストアドプロシージャの名前 |
| `parameters` | object | × | プロシージャのパラメータ |
| `defaultCatalog` | string | × | デフォルトのカタログ名 |
| `defaultSchema` | string | × | デフォルトのスキーマ名 |
| `timeout` | integer | × | タイムアウト秒数（1～300秒） |

### プロシージャパラメータ

各パラメータは以下の形式で指定します：

```json
{
  "parameterName": {
    "direction": <1, 2, 4, または 5>,
    "dataType": <1～18の整数値>,
    "value": <パラメータの値>
  }
}
```

**パラメータ方向：**
- 1: INPUT（入力）
- 2: OUTPUT（出力）
- 4: INOUT（入出力）
- 5: RETURN（戻り値）

**リクエスト例：**

```json
{
  "procedure": "GetCustomerById",
  "defaultCatalog": "Salesforce1",
  "parameters": {
    "CustomerId": {
      "direction": 1,
      "dataType": 5,
      "value": "12345"
    }
  }
}
```

### レスポンス

**ステータス：** 200 OK

```json
{
  "results": [{
    "affectedRows": -1,
    "schema": [...],
    "rows": [...]
  }],
  "parameters": {
    "OutputParam": "value"
  },
  "error": null
}
```

---

## SQL構文

CData Connect AIは、**SQL-92標準**に基づいたSQL構文をサポートしています。

### 識別子のクォート

テーブル名やカラム名などの識別子は、`[]`文字を使用してクォートします：

```sql
SELECT [FirstName], [LastName] FROM [Customers]
```

### ブール値

ブール値は `1`（TRUE）と `0`（FALSE）を使用します：

```sql
SELECT * FROM [Users] WHERE [IsActive] = 1
```

### サポートされるSQL句

- `SELECT`
- `FROM`
- `WHERE`
- `INNER JOIN`
- `LEFT JOIN`
- `GROUP BY`
- `HAVING`
- `ORDER BY`
- `LIMIT` / `OFFSET`

### サポートされる演算子

- 比較演算子: `=`, `<>`, `<`, `>`, `<=`, `>=`
- パターンマッチ: `LIKE`
- リスト: `IN`
- 範囲: `BETWEEN`

### サポートされる集約関数

- `COUNT()`
- `SUM()`
- `AVG()`
- `MIN()`
- `MAX()`

### サポートされるSQL文

- `SELECT` - データの取得
- `INSERT` - データの挿入
- `UPDATE` - データの更新
- `DELETE` - データの削除
- `EXEC` - ストアドプロシージャの実行（`/exec`エンドポイント推奨）

---

## パラメータ化クエリのベストプラクティス

セキュリティを確保し、SQLインジェクションを防ぐために、パラメータ化クエリの使用が強く推奨されます。

**推奨される方法：**

```sql
SELECT * FROM [Customers] WHERE [CustomerId] = @CustomerId
```

**推奨されない方法（SQLインジェクションのリスク）：**

```sql
SELECT * FROM [Customers] WHERE [CustomerId] = '12345'
```

---

[← トップに戻る](./README.md)
