# アカウントAPI

## アカウント作成

子アカウントを作成します。

### エンドポイント

```http
POST /poweredby/account/create
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
| `externalId` | string | ○ | 作成するアカウントの外部識別子 |

**リクエスト例：**

```json
{
  "externalId": "MyExternalId"
}
```

### レスポンス

**ステータス：** 200 OK

**返却フィールド：**

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `accountId` | string | Connect AIの内部アカウントID |
| `externalId` | string | 顧客の識別子 |
| `createdTime` | date-time | アカウント作成日時（ISO 8601形式） |

**レスポンス例：**

```json
{
  "accountId": "8744e71e-ee33-4d4e-916f-0a21eba65902",
  "externalId": "MyExternalId",
  "createdTime": "2024-07-10T19:10:52.139Z"
}
```

---

[← トップに戻る](./README.md)
