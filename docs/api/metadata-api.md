# メタデータAPI

## 概要

メタデータAPIは、接続されたデータソースについての情報を取得するためのエンドポイントを提供します。メタデータとは、データを説明する情報（スキーマ、テーブル、カラム、キーなど）を指します。

すべてのメタデータAPIエンドポイントは以下の共通仕様を持ちます：

- **HTTPメソッド**: GET
- **認証**: Basic認証（PATをパスワードとして使用）
- **レスポンス形式**: JSON（QueryResultオブジェクト）

---

## 1. カタログ一覧取得

ユーザーがアカウントに設定した接続（カタログ）の一覧を取得します。

### エンドポイント

```http
GET /catalogs
```

### クエリパラメータ

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `workspace` | string | × | 特定のワークスペースに結果を制限 |

### レスポンス例

```json
{
  "results": [{
    "affectedRows": -1,
    "schema": [{
      "catalogName": "CData",
      "columnLabel": "TABLE_CATALOG",
      "columnName": "TABLE_CATALOG",
      "dataType": 5,
      "dataTypeName": "VARCHAR"
    }],
    "rows": [["Salesforce1"]]
  }]
}
```

---

## 2. スキーマ一覧取得

指定したカタログのスキーマ一覧を取得します。

### エンドポイント

```http
GET /schemas
```

### クエリパラメータ

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `workspace` | string | × | 特定のワークスペースに結果を制限 |
| `catalogName` | string | × | 特定のカタログに結果を制限 |
| `schemaName` | string | × | 特定のスキーマに結果を制限 |

### レスポンス構造

```json
{
  "results": [{
    "affectedRows": -1,
    "schema": [...],
    "rows": [...]
  }],
  "error": null
}
```

---

## 3. テーブル一覧取得

スキーマ内のテーブルとビューの一覧を取得します。

### エンドポイント

```http
GET /tables
```

### クエリパラメータ

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `workspace` | string | × | 特定のワークスペースに結果を制限 |
| `catalogName` | string | × | 特定のカタログに結果を制限 |
| `schemaName` | string | × | 特定のスキーマに結果を制限 |
| `tableName` | string | × | 特定のテーブルに結果を制限 |
| `tableType` | string | × | 特定のテーブルタイプに結果を制限 |

---

## 4. カラム一覧取得

テーブルのカラム情報を取得します。

### エンドポイント

```http
GET /columns
```

### クエリパラメータ

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `workspace` | string | × | 特定のワークスペースに結果を制限 |
| `catalogName` | string | × | 特定のカタログに結果を制限 |
| `schemaName` | string | × | 特定のスキーマに結果を制限 |
| `tableName` | string | × | 特定のテーブルに結果を制限 |
| `columnName` | string | × | 特定のカラムに結果を制限 |

### カラム情報に含まれる属性

- `catalogName` - カタログ名
- `columnLabel` - カラムラベル
- `columnName` - カラム名
- `dataType` - データ型（整数値1～18）
- `dataTypeName` - データ型名
- `length` - データ長
- `nullable` - NULL許可フラグ
- `ordinal` - カラムの順序
- `precision` - 精度
- `scale` - スケール
- `schemaName` - スキーマ名
- `tableName` - テーブル名

---

## 5. プライマリキー一覧取得

テーブルのプライマリキーに関する情報を取得します。

### エンドポイント

```http
GET /primaryKeys
```

### クエリパラメータ

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `workspace` | string | × | 特定のワークスペースに結果を制限 |
| `catalogName` | string | × | 特定のカタログに結果を制限 |
| `schemaName` | string | × | 特定のスキーマに結果を制限 |
| `tableName` | string | × | 特定のテーブルに結果を制限 |

---

## 6. エクスポートキー一覧取得

テーブルの主キーで参照される外部キーに関する情報を取得します。

### エンドポイント

```http
GET /exportedKeys
```

### クエリパラメータ

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `workspace` | string | × | 特定のワークスペースに結果を制限 |
| `catalogName` | string | × | 特定のカタログに結果を制限 |
| `schemaName` | string | × | 特定のスキーマに結果を制限 |
| `tableName` | string | × | 特定のテーブルに結果を制限 |

---

## 7. インポートキー一覧取得

テーブルの外部キーによって参照されるプライマリキーについての情報を取得します。

### エンドポイント

```http
GET /importedKeys
```

### クエリパラメータ

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `workspace` | string | × | 特定のワークスペースに結果を制限 |
| `catalogName` | string | × | 特定のカタログに結果を制限 |
| `schemaName` | string | × | 特定のスキーマに結果を制限 |
| `tableName` | string | × | 特定のテーブルに結果を制限 |

---

## 8. プロシージャ一覧取得

指定したスキーマのストアドプロシージャに関する情報を取得します。

### エンドポイント

```http
GET /procedures
```

### クエリパラメータ

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `workspace` | string | × | 特定のワークスペースに結果を制限 |
| `catalogName` | string | × | 特定のカタログに結果を制限 |
| `schemaName` | string | × | 特定のスキーマに結果を制限 |
| `procedureName` | string | × | 特定のプロシージャに結果を制限 |

---

## 9. プロシージャパラメータ一覧取得

ストアドプロシージャのパラメータに関する情報を取得します。

### エンドポイント

```http
GET /procedureParameters
```

### クエリパラメータ

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `workspace` | string | × | 特定のワークスペースに結果を制限 |
| `catalogName` | string | × | 特定のカタログに結果を制限 |
| `schemaName` | string | × | 特定のスキーマに結果を制限 |
| `procedureName` | string | × | 特定のプロシージャに結果を制限 |
| `paramName` | string | × | 特定のパラメータ名に結果を制限 |

---

[← トップに戻る](./README.md)
