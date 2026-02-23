# CData Connect AI Embedded Cloud API リファレンス

CData Connect AI Embedded Cloud のAPI仕様をまとめたリファレンスです。

## 目次

1. [API概要](./overview.md) - 目的、主要機能、アーキテクチャ
2. [認証](./authentication.md) - JWT認証、鍵生成、セキュリティ要件
3. [REST API基本仕様](./rest-api-basics.md) - リクエスト/レスポンス形式、エラーハンドリング
4. [アカウントAPI](./account-api.md) - アカウント作成
5. [接続API](./connection-api.md) - 接続作成とリダイレクト
6. [監査API](./audit-api.md) - 監査ログ取得
7. [メタデータAPI](./metadata-api.md) - スキーマ、テーブル、カラム情報の取得
8. [SQL API](./sql-api.md) - クエリ実行、バッチ操作、プロシージャ実行
9. [MCP API](./mcp-api.md) - Model Context Protocol による AI アシスタント連携（Streamable HTTP）

## ベースURL

```
https://cloud.cdata.com/api
```

## クイックスタート

### 1. 認証トークンの取得

まず、[認証ガイド](./authentication.md)を参照してJWTトークンを生成します。

### 2. データソースの接続

[接続API](./connection-api.md)を使用してデータソースへの接続を作成します。

### 3. メタデータの取得

[メタデータAPI](./metadata-api.md)を使用して、接続したデータソースのスキーマ、テーブル、カラム情報を取得します。

### 4. データのクエリ

[SQL API](./sql-api.md)を使用してデータをクエリします。

### 5. AI アシスタントとの連携

[MCP API](./mcp-api.md)を使用して、Claude などの AI モデルからデータに自然言語でアクセスします。

## 参考リンク

- [CData Connect AI 公式ドキュメント](https://docs.cloud.cdata.com/ja/API/API-Embedded)
- [認証ドキュメント](https://docs.cloud.cdata.com/ja/API/Authentication-Embedded)
- [REST APIドキュメント](https://docs.cloud.cdata.com/ja/API/REST-API-Embedded)
- [完全なドキュメントインデックス](https://docs.cloud.cdata.com/llms.txt)

---

**最終更新日：** 2026-02-23
