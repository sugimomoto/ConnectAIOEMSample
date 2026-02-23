# 接続API

## 接続作成

データソースへの接続を作成し、ユーザーをリダイレクトするためのURLを取得します。

### エンドポイント

```http
POST /poweredby/connection/create
```

### リクエスト

**ヘッダー：**
```http
Authorization: Bearer {JWT_TOKEN}
Content-Type: application/json
```

**パラメータ：**

| パラメータ | 型 | 必須 | 説明 |
|----------|-----|------|------|
| `dataSource` | string | × | データソースの種類（例：Snowflake、ActOn、Salesforce） |
| `redirectURL` | string | ○ | ユーザーが接続作成後にリダイレクトされるURL |
| `name` | string | × | 接続の名前（オプション） |

**リクエスト例：**

```json
{
  "dataSource": "Salesforce",
  "redirectURL": "https://example.com/callback",
  "name": "My Salesforce Connection"
}
```

### レスポンス

**ステータス：** 200 OK

**返却フィールド：**

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `redirectURL` | string | ユーザーをリダイレクトするURL |

**レスポンス例：**

```json
{
  "redirectURL": "https://cloud.cdata.com/connect/..."
}
```

### 使用フロー

1. アプリケーションから `/poweredby/connection/create` エンドポイントを呼び出す
2. レスポンスで返された `redirectURL` にユーザーをリダイレクト
3. ユーザーがCData Connect AIの画面でデータソースの認証情報を入力
4. 接続が完了したら、指定した `redirectURL` にユーザーがリダイレクトされる

---

[← トップに戻る](./README.md)
