# 認証

## 認証方式

CData Connect AI APIは、**JSON Web Token (JWT)** を使用したRSA 256ベースの認証が必須です。

## トークン取得方法

### 基本的なステップ

1. **ヘッダー作成**: `{"alg": "RS256", "typ": "JWT"}` 形式で設定
2. **Base64url エンコード**: ヘッダーをエンコード
3. **クレームセット構築**: 必須パラメータを含むJSONを作成
4. **署名**: 秘密鍵でトークンに署名

### 必須クレームパラメータ

| パラメータ | 説明 |
|-----------|------|
| `tokenType` | "powered-by" に固定 |
| `iat` | トークン発行時刻（UNIXタイムスタンプ） |
| `exp` | トークン有効期限（UNIXタイムスタンプ） |
| `iss` | 親アカウントID |
| `sub` | 子アカウントID（オプション） |

### トークン形式

```
Base64UrlEncode(ヘッダ) + "." + Base64UrlEncode(クレーム) + "." + 署名
```

## セキュリティ要件

### 鍵生成方法

```bash
# 秘密鍵の生成
openssl genrsa -out ./private.key 4096

# 公開鍵の生成（秘密鍵から）
openssl rsa -in ./private.key -pubout -out ./public.key
```

**注意事項：**
- 公開鍵をCDataに登録する必要があります（サポートチケット経由）
- 秘密鍵は安全に保管し、外部に公開しないこと

## 認証ヘッダー

APIリクエストには、以下の形式で認証ヘッダーを含める必要があります：

```http
Authorization: Bearer {JWT_TOKEN}
```

## Basic認証（メタデータAPI用）

メタデータAPIエンドポイントでは、Basic認証を使用します：

```http
Authorization: Basic {BASE64_ENCODED_CREDENTIALS}
```

**認証情報：**
- ユーザー名: 任意（通常は空文字列またはユーザー名）
- パスワード: PAT（Personal Access Token）

PATは、Connect AIの **Settings > Access Tokens** から取得できます。

---

[← トップに戻る](./README.md)
