# ユビキタス言語定義: DataHub - Connect AI OEM リファレンス実装

**バージョン**: 1.0
**最終更新**: 2026-02-22

---

## 概要

本ドキュメントは、プロジェクト内で使用するすべての用語を定義します。
ドキュメント・コード・会話のすべてで同じ言葉を同じ意味で使うことを目的とします。

---

## 目次

1. [ビジネス・ドメイン用語](#1-ビジネスドメイン用語)
2. [CData Connect AI 用語](#2-cdata-connect-ai-用語)
3. [データ構造用語](#3-データ構造用語)
4. [認証・セキュリティ用語](#4-認証セキュリティ用語)
5. [UI/UX用語](#5-uiux用語)
6. [英語・日本語対応表](#6-英語日本語対応表)
7. [コード上の命名規則まとめ](#7-コード上の命名規則まとめ)

---

## 1. ビジネス・ドメイン用語

### DataHub（データハブ）

本プロジェクトのアプリケーション名。
CData Connect AI OEM を活用したデータ統合・探索・クエリ実行のリファレンス実装。

### OEMパターン（OEM Pattern）

CData Connect AI を自社アプリケーションに組み込む開発形態。
アプリケーション開発者（OEMパートナー）がエンドユーザーに対してデータ連携機能を提供する。

```
[OEMパートナー（本プロジェクト）] → [エンドユーザー] → [データソース]
                    ↑
         CData Connect AI Embedded Cloud を利用
```

### ユーザー（User）

DataHubアプリケーションの利用者。
メールアドレス・パスワードで登録し、自分のデータソースへの接続を管理する。
各ユーザーには対応する **子アカウント（Child Account）** が Connect AI に作成される。

### コネクション（Connection）

ユーザーが作成するデータソースへの接続定義。
接続先のデータソース種別（`data_source`）と識別名（`name`）を保持する。
データソースの認証情報（パスワード・APIキー等）は **Connect AI が管理** し、本アプリでは保持しない。

### データソース（Data Source）

接続先のSaaS・データベースの種別。例: `Salesforce`, `QuickBooks`, `AzureDevOps`。
Connect AI Connection APIの `dataSource` パラメータに指定する値。

### 保存済みクエリ（Saved Query）

ユーザーが作成・保存したクエリ定義。クエリビルダーで作成し、再実行できる。
（Phase 3以降の機能）

---

## 2. CData Connect AI 用語

### CData Connect AI Embedded Cloud

CData Softwareが提供するデータ接続・統合サービス。
本プロジェクトでは HTTP REST APIを通じて利用する。

### 親アカウント（Parent Account）/ ParentAccountId

CDataとの契約により **OEMパートナー（本プロジェクト）** に対して発行されるCData Connect AIのアカウント。
アプリ開発者が事前に取得・保持するものであり、エンドユーザーには関係しない。

- 子アカウントの作成・管理権限を持つ
- RSA秘密鍵でJWTを署名してAPIを呼び出す
- `ParentAccountId` は JWT の `iss`（issuer）クレームに設定する

環境変数: `CONNECT_AI_PARENT_ACCOUNT_ID`

> **混同注意**: `ParentAccountId` はパートナー1者に1つ発行される固定値。エンドユーザーごとに変わるものではない。

### 子アカウント（Child Account）/ ChildAccountId

**DataHubのエンドユーザーが登録したとき**に、親アカウント配下に自動作成されるCData Connect AIのアカウント。
Connect AIにおけるテナント分離の単位となる。

- ユーザー登録時に **Account API** (`POST /poweredby/account/create`) を呼び出して作成される
- 作成時に `externalId`（本アプリの `users.email`）を指定する
- Connect AIから返却される `ChildAccountId` を `users.connect_ai_account_id` カラムに保存する
- `ChildAccountId` は JWT の `sub`（subject）クレームに設定する

> **混同注意**: `ChildAccountId` はエンドユーザー1人に1つ発行される。`ParentAccountId` とは別物。

### externalId（外部ID）

子アカウント作成時にOEMパートナーが指定する識別子。Connect AI側でユーザーを特定するための参照キー。
本プロジェクトでは `users.email`（メールアドレス）を使用する。環境再構築時も値が変わらず、DB の `UNIQUE` 制約により衝突しない。

```python
external_id = user.email  # 例: "alice@example.com"
```

### ChildAccountId（子アカウントID）

Connect AIが子アカウントに発行する識別子（UUID形式）。
Account API のレスポンスフィールド名は `accountId` だが、本プロジェクトでは `ParentAccountId` との混同を避けるため **`ChildAccountId`** と呼ぶ。

| 用途 | 値 |
|------|-----|
| JWTの `sub` クレーム | `ChildAccountId` |
| DB保存先カラム | `users.connect_ai_account_id` |
| API レスポンスでのフィールド名 | `accountId`（Connect AI側の表記） |

### コネクション名（Connection Name） / catalogName（カタログ名）

Connect AI Connection APIの `name` パラメータに指定した値が、
その後のMetadata API・SQL APIで **`catalogName`** として使用される。

```
Connection API: name = "MySalesforce"
    ↓
Metadata API: catalogName = "MySalesforce"
SQL API:      defaultCatalog = "MySalesforce"
SQL クエリ:   SELECT [Name] FROM [MySalesforce].[dbo].[Account]
```

> **注意**: コネクション名にはスペースや特殊文字を避け、英数字・ハイフン・アンダースコアのみ使用すること。

### redirectURL（リダイレクトURL）

Connection API呼び出し時に指定するコールバックURL。
ユーザーが Connect AI 側でデータソースの認証情報を入力・完了した後に、このURLへリダイレクトされる。

**本プロジェクトでの値:**
```
http://localhost:5000/callback?connectionId={connection.id}
```

### コネクションステータス（Connection Status）

コネクションの現在の状態を示す。

| ステータス | 意味 |
|----------|------|
| `pending` | Connect AI側での認証情報の入力が未完了 |
| `active` | 認証完了。データソースへのアクセスが可能 |
| `error` | 接続エラーが発生 |

### Account API

子アカウントを作成するAPI。ユーザー登録時に呼び出す。

```
POST /poweredby/account/create
```

### Connection API

コネクションを作成し、認証UIへのリダイレクトURLを取得するAPI。

```
POST /poweredby/connection/create
```

### Metadata API

データソースのスキーマ情報（カタログ・スキーマ・テーブル・カラム）を取得するAPI。
Basic認証（`accountId:password`）またはBearerトークンで呼び出す。

```
GET /catalogs
GET /schemas
GET /tables
GET /columns
GET /primaryKeys
```

### SQL API

データソースに対してSQLクエリを実行するAPI。

```
POST /query   # SELECT / INSERT / UPDATE / DELETE
POST /batch   # バッチINSERT/UPDATE/DELETE
POST /exec    # ストアドプロシージャ実行
```

---

## 3. データ構造用語

### カタログ（Catalog）

Connect AI のデータ階層の最上位レベル。通常は **コネクション名** に対応する。

```
Catalog（= コネクション名）
  └── Schema
        └── Table
              └── Column
```

### スキーマ（Schema）

カタログ配下のグループ化単位。データソースによって意味が異なる。
例: Salesforceでは `dbo`、データベースでは `public` など。

### テーブル（Table）

スキーマ配下のデータテーブル。実際のレコードが格納される単位。

### カラム（Column）

テーブルを構成するフィールド定義。名前・データ型・NULL可否・主キー等の情報を持つ。

### プライマリキー（Primary Key）

テーブル内のレコードを一意に識別するカラム。CRUD操作（UPDATE/DELETE）時のWHERE条件として使用。

### パラメータ化クエリ（Parameterized Query）

SQLの値部分を `@パラメータ名` で置き換え、値を別途指定するクエリ形式。
SQLインジェクション攻撃を防ぐため、本プロジェクトでは**必須**とする。

```python
# パラメータ化クエリの例
query = "SELECT [Name] FROM [Account] WHERE [Id] = @id"
parameters = {"id": {"dataType": 5, "value": "001xx000003GYn1"}}
```

### データ型 ID（Data Type ID）

Connect AI SQL APIで使用するデータ型の数値識別子。

| ID | 型名 | 用途 |
|----|------|------|
| 3 | INTEGER | 整数値 |
| 5 | VARCHAR | 文字列（最も一般的） |
| 7 | DOUBLE | 浮動小数点数 |
| 9 | DATE | 日付 |
| 10 | TIME | 時刻 |
| 11 | TIMESTAMP | 日時 |
| 14 | BIT | 真偽値 |
| 18 | BIGINT | 大整数 |

詳細は [docs/api/rest-api-basics.md](./api/rest-api-basics.md) を参照。

---

## 4. 認証・セキュリティ用語

### JWT（JSON Web Token）

認証情報をJSON形式でエンコードしたトークン。本プロジェクトでは2種類使用する。

| 種別 | 用途 | アルゴリズム | 署名鍵 |
|------|------|------------|-------|
| **アプリJWT** | ブラウザ↔バックエンドの認証 | HS256 | `SECRET_KEY`（対称鍵） |
| **Connect AI JWT** | バックエンド↔Connect AI APIの認証 | RS256 | `CONNECT_AI_PRIVATE_KEY`（RSA秘密鍵） |

### アプリJWT（App JWT）

バックエンドが発行し、フロントエンド（ブラウザ）が保持するJWTトークン。
`Authorization: Bearer {token}` ヘッダーで送信される。

**ペイロード:**
```json
{
  "user_id": 1,
  "exp": 1709212800
}
```

### Connect AI JWT

バックエンドがConnect AI APIを呼び出す際に生成するJWTトークン。
RS256（RSA署名）を使用し、親アカウントの秘密鍵で署名する。

**ペイロード:**
```json
{
  "tokenType": "powered-by",
  "iat": 1709208800,
  "exp": 1709212800,
  "iss": "ParentAccountId",
  "sub": "ChildAccountId"
}
```

### bcrypt

パスワードハッシュ化に使用するアルゴリズム。
ソルト付きハッシュを生成し、同じパスワードでも毎回異なるハッシュ値になる。

```python
# cost factor: 10（計算コストのバランス設定）
bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=10))
```

### テナント分離（Tenant Isolation）

マルチユーザー環境において、各ユーザーが他のユーザーのデータにアクセスできないようにする仕組み。
本プロジェクトでは、すべてのDBクエリに `user_id = current_user.id` フィルタを付与して実現する。

### RSA鍵ペア（RSA Key Pair）

Connect AI JWT署名に使用する公開鍵・秘密鍵のペア。

| 鍵 | 管理場所 | 用途 |
|---|---------|------|
| 秘密鍵（Private Key） | `.env` の `CONNECT_AI_PRIVATE_KEY` | JWT署名（バックエンドのみ保持） |
| 公開鍵（Public Key） | CData側に登録 | JWT検証（CData側が実施） |

---

## 5. UI/UX用語

### ダッシュボード（Dashboard）

ログイン後の最初の画面。各機能へのナビゲーションと概要情報を表示する。
URL: `/dashboard`

### コネクション管理（Connection Management）

ユーザーが保有するコネクションの一覧表示・新規作成・削除を行う画面。
URL: `/connections`

### メタデータエクスプローラー（Metadata Explorer）

データソースのスキーマ構造（カタログ→スキーマ→テーブル→カラム）をドリルダウン形式で探索する画面。
URL: `/explorer`

### クエリビルダー（Query Builder）

GUIでSELECTクエリを構築し、結果を表示・エクスポートする画面。
URL: `/query-builder`

### データブラウザ（Data Browser）

テーブルのレコード一覧表示とCRUD操作（作成・読取・更新・削除）を行う画面。
URL: `/data-browser`

### コールバック画面（Callback）

Connect AI認証完了後にリダイレクトされる画面。
URLパラメータの `connectionId` を使用してコネクションを有効化（`activate`）する。
URL: `/callback?connectionId={id}`

### ブレッドクラム（Breadcrumb）

メタデータエクスプローラーでの現在位置を示すナビゲーション。
例: `MySalesforce > dbo > Account`

---

## 6. 英語・日本語対応表

### アプリケーション固有用語

| 英語 | 日本語 | コードでの表記 |
|------|--------|-------------|
| User | ユーザー | `User`（モデル）, `user_id`（カラム） |
| Connection | コネクション | `Connection`（モデル）, `connection_id`（カラム） |
| Data Source | データソース | `data_source`（カラム・パラメータ） |
| Saved Query | 保存済みクエリ | `SavedQuery`（モデル）, `saved_query_id` |
| Connection Status | コネクションステータス | `status`（カラム） |

### Connect AI API用語

| 英語 | 日本語 | コードでの表記 |
|------|--------|-------------|
| Parent Account / ParentAccountId | 親アカウント | `CONNECT_AI_PARENT_ACCOUNT_ID`（環境変数）, JWT `iss` クレーム |
| Child Account / ChildAccountId | 子アカウント | `connect_ai_account_id`（DBカラム）, JWT `sub` クレーム |
| External ID | 外部ID | `externalId`（Account APIパラメータ） |
| accountId | ―（本プロジェクトでは ChildAccountId と呼ぶ） | Account APIレスポンスのフィールド名 |
| Redirect URL | リダイレクトURL | `redirectURL`（APIパラメータ・レスポンス） |
| Catalog | カタログ | `catalogName`（APIパラメータ） |
| Schema | スキーマ | `schemaName`（APIパラメータ） |
| Table | テーブル | `tableName`（APIパラメータ） |
| Column | カラム | `columnName`（APIパラメータ） |
| Parameterized Query | パラメータ化クエリ | `parameters`（APIパラメータ） |

### 認証・技術用語

| 英語 | 日本語 | コードでの表記 |
|------|--------|-------------|
| Authentication | 認証 | `auth`（モジュール・URL） |
| Authorization | 認可 | `Authorization`（HTTPヘッダー） |
| JSON Web Token | JWT | `token`（変数）, `jwt_token`（localStorage） |
| Password Hash | パスワードハッシュ | `password_hash`（カラム） |
| Tenant Isolation | テナント分離 | （コメント・設計用語） |

### 画面・機能名

| 英語 | 日本語 | URLパス |
|------|--------|--------|
| Login | ログイン | `/login` |
| Register | ユーザー登録 | `/register` |
| Dashboard | ダッシュボード | `/dashboard` |
| Connection Management | コネクション管理 | `/connections` |
| Metadata Explorer | メタデータエクスプローラー | `/explorer` |
| Query Builder | クエリビルダー | `/query-builder` |
| Data Browser | データブラウザ | `/data-browser` |
| Callback | コールバック | `/callback` |

---

## 7. コード上の命名規則まとめ

### DBカラム名とAPIフィールド名の対応

同じ概念でもDB（Python）側とAPI（JSON）側で表記が異なる場合があります。

| 概念 | DBカラム名（Python） | APIフィールド名（JSON） |
|------|---------------------|----------------------|
| ChildAccountId（Connect AI子アカウントID） | `connect_ai_account_id` | `connect_ai_account_id` |
| データソース | `data_source` | `data_source` |
| リダイレクトURL | ―（DBに保存しない） | `redirectURL` |
| コネクションステータス | `status` | `status` |
| 作成日時 | `created_at` | `created_at` |

### 注意: Connect AI APIとのフィールド名の違い

Connect AI APIはキャメルケース（`redirectURL`, `accountId`）を使用しますが、
本アプリ内部ではスネークケース（`redirect_url`, `connect_ai_account_id`）を使用します。
特に `accountId`（Connect AI側の表記）は本プロジェクトでは `ChildAccountId` と呼び、DBカラム名は `connect_ai_account_id` です。
Connect AI APIとの入出力時に変換が発生する箇所に注意してください。

```python
# Connect AI APIへのリクエスト（キャメルケース）
payload = {
    "dataSource": data_source,
    "redirectURL": redirect_url,
    "name": name,
}

# レスポンスの受け取り（キャメルケース → 内部変数はスネークケース）
connect_ai_account_id = response["accountId"]
```

---

**承認者**: _________________
**承認日**: _________________
