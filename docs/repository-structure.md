# リポジトリ構造定義書: DataHub - Connect AI OEM リファレンス実装

**バージョン**: 1.0
**最終更新**: 2026-02-22

---

## 目次

1. [全体構成](#1-全体構成)
2. [ルートディレクトリ](#2-ルートディレクトリ)
3. [backend/](#3-backend)
4. [frontend/](#4-frontend)
5. [docs/](#5-docs)
6. [.steering/](#6-steering)
7. [ファイル配置ルール](#7-ファイル配置ルール)
8. [命名規則](#8-命名規則)

---

## 1. 全体構成

```
ConnectAIOEMSample/                     # リポジトリルート
├── backend/                            # Pythonバックエンド
├── frontend/                           # HTML/CSS/JSフロントエンド
├── docs/                               # 永続的ドキュメント
├── .steering/                          # 作業単位のドキュメント
├── .env.example                        # 環境変数のサンプル（コミット対象）
├── .gitignore                          # Git除外設定
├── CLAUDE.md                           # AI開発ガイド（プロジェクトメモリ）
└── README.md                           # プロジェクト説明
```

---

## 2. ルートディレクトリ

| ファイル/ディレクトリ | 役割 | コミット |
|----------------------|------|---------|
| `backend/` | Flaskアプリケーション本体 | ✓ |
| `frontend/` | HTML/JS/CSSファイル群 | ✓ |
| `docs/` | 永続的なプロジェクトドキュメント | ✓ |
| `.steering/` | 作業単位の設計・タスクドキュメント | ✓ |
| `.env.example` | 環境変数のテンプレート（実値なし） | ✓ |
| `.env` | 実際の環境変数（秘密情報を含む） | **✗ gitignore** |
| `.gitignore` | Git管理対象外の定義 | ✓ |
| `CLAUDE.md` | Claude Code向け開発ガイドライン | ✓ |
| `README.md` | セットアップ手順、プロジェクト概要 | ✓ |

---

## 3. backend/

Flaskアプリケーションのすべてのコードを格納します。

```
backend/
├── app.py                              # アプリケーションエントリーポイント
├── config.py                           # 環境別設定クラス
├── models/                             # SQLAlchemyモデル
│   ├── __init__.py                     # DBインスタンス生成・モデルのエクスポート
│   ├── user.py                         # Userモデル
│   └── connection.py                   # Connectionモデル
├── schemas/                            # Pydanticスキーマ（リクエスト/レスポンス検証）
│   ├── __init__.py
│   ├── user_schema.py                  # ユーザー登録・ログインのスキーマ
│   ├── connection_schema.py            # コネクション作成のスキーマ
│   └── query_schema.py                 # クエリ実行のスキーマ
├── services/                           # ビジネスロジック層
│   ├── __init__.py
│   ├── auth_service.py                 # 認証・Connect AI Account API
│   ├── connection_service.py           # コネクション管理・Connection API
│   ├── metadata_service.py             # Metadata API呼び出し
│   └── query_service.py                # SQL API呼び出し
├── connectai/                          # Connect AI APIクライアント
│   ├── __init__.py
│   ├── client.py                       # HTTP APIクライアント（requests）
│   ├── jwt.py                          # Connect AI用JWT生成（RS256）
│   └── exceptions.py                   # Connect AI固有の例外クラス
├── api/                                # HTTPルーティング・エンドポイント定義
│   ├── __init__.py
│   └── v1/                             # APIバージョン1
│       ├── __init__.py                 # Blueprint登録
│       ├── auth.py                     # POST /api/v1/auth/*
│       ├── connections.py              # /api/v1/connections/*
│       ├── metadata.py                 # GET /api/v1/metadata/*
│       └── queries.py                  # POST /api/v1/queries/*
├── middleware/                         # リクエスト前処理
│   ├── __init__.py
│   ├── auth.py                         # JWT検証デコレータ（@require_auth）
│   └── error_handler.py                # グローバルエラーハンドラー
├── migrations/                         # Alembicマイグレーション
│   ├── alembic.ini
│   ├── env.py
│   └── versions/                       # マイグレーションスクリプト
├── tests/                              # ユニット・インテグレーションテスト
│   ├── __init__.py
│   ├── conftest.py                     # pytestの共通フィクスチャ
│   ├── test_auth.py                    # 認証APIのテスト
│   ├── test_connections.py             # コネクションAPIのテスト
│   ├── test_metadata.py                # メタデータAPIのテスト
│   └── test_queries.py                 # クエリAPIのテスト
├── requirements.txt                    # 本番依存パッケージ
├── requirements-dev.txt                # 開発用依存パッケージ（pytest等）
└── .env.example                        # バックエンド環境変数テンプレート
```

### 3.1 各ディレクトリの役割

#### backend/app.py
- Flaskアプリケーションの生成・初期化
- Blueprintの登録
- フロントエンドの静的ファイル・HTMLテンプレートの提供

```python
# 静的ファイルとテンプレートの設定例
app = Flask(
    __name__,
    static_folder='../frontend/static',
    template_folder='../frontend/pages'
)
```

#### backend/config.py
- 環境変数の読み込みと設定クラスの定義
- `DevelopmentConfig`（DEBUG=True）のみ定義（デモ用途のため）

#### backend/models/
- SQLAlchemyモデルクラスを1ファイルにつき1モデルで定義
- `__init__.py` で `db = SQLAlchemy()` インスタンスを生成し、各モデルをインポート

#### backend/schemas/
- Pydanticモデルによるリクエスト/レスポンスのバリデーション
- APIエンドポイントでの入力検証に使用

#### backend/services/
- ビジネスロジックをAPIルーティングから分離
- データベース操作・外部API呼び出しを担当
- Blueprintから直接データベースやAPIを操作しない（serviceを経由する）

#### backend/connectai/
- CData Connect AI APIとの通信を担当するモジュール
- `client.py`: HTTP APIクライアント（`requests`ライブラリを使用）
- `jwt.py`: RS256署名のJWTトークン生成
- `exceptions.py`: APIエラーを表すカスタム例外

#### backend/api/v1/
- Flaskの `Blueprint` を使用したエンドポイント定義
- HTTP層のみ（リクエスト/レスポンスの処理）。ビジネスロジックはservices/に委譲

#### backend/middleware/
- `auth.py`: `@require_auth` デコレータ（JWTトークン検証）
- `error_handler.py`: 未処理の例外をJSONエラーレスポンスに変換

---

## 4. frontend/

ブラウザで動作するUIのすべてのファイルを格納します。
Flaskが静的ファイルサーバーとして配信します（ビルドステップなし）。

```
frontend/
├── pages/                              # HTMLテンプレート（Flaskが render_template で使用）
│   ├── login.html                      # ログイン画面
│   ├── register.html                   # ユーザー登録画面
│   ├── dashboard.html                  # ダッシュボード
│   ├── connections.html                # コネクション管理画面
│   ├── explorer.html                   # メタデータエクスプローラー
│   ├── query-builder.html              # クエリビルダー
│   ├── data-browser.html               # データブラウザ（CRUD）
│   └── callback.html                   # コネクション認証コールバック画面
└── static/                             # 静的ファイル（/static/ でアクセス可能）
    ├── css/
    │   └── custom.css                  # カスタムスタイル（Tailwind補完用）
    ├── js/
    │   ├── api-client.js               # バックエンドAPIとの通信クラス
    │   ├── auth.js                     # 認証処理（ログイン/ログアウト/JWT管理）
    │   ├── connections.js              # コネクション管理UI
    │   ├── explorer.js                 # メタデータエクスプローラーUI
    │   ├── query-builder.js            # クエリビルダーUI
    │   ├── data-browser.js             # データブラウザUI（CRUD操作）
    │   └── utils.js                    # 共通ユーティリティ関数
    └── img/
        └── logo.svg                    # ロゴ画像
```

### 4.1 各ファイルの役割

#### frontend/pages/
- 各画面のHTMLファイル
- Tailwind CSS・Alpine.jsはCDN経由で読み込む（ビルド不要）
- `<script src="/static/js/xxx.js">` でJavaScriptを読み込む

#### frontend/static/css/
- `custom.css`: Tailwindのユーティリティで表現できないカスタムスタイルのみ記述

#### frontend/static/js/
- 各JSファイルは対応するHTMLページで読み込む
- `api-client.js` は全ページで共通使用
- `auth.js` は認証状態の確認・管理を担当し、全保護ページで読み込む

#### frontend/static/img/
- SVG形式を優先（スケーラブル、軽量）
- PNG形式はアイコンやロゴの代替形式として使用

---

## 5. docs/

アプリケーション全体の設計を定義する永続的なドキュメント。

```
docs/
├── product-requirements.md             # プロダクト要求定義書
├── functional-design.md                # 機能設計書
├── architecture.md                     # 技術仕様書
├── repository-structure.md             # リポジトリ構造定義書（本ドキュメント）
├── development-guidelines.md           # 開発ガイドライン
├── glossary.md                         # ユビキタス言語定義
└── api/                                # CData Connect AI APIリファレンス
    ├── README.md                       # APIリファレンス目次
    ├── overview.md                     # API概要
    ├── authentication.md               # 認証方式
    ├── rest-api-basics.md              # REST APIの基本仕様
    ├── account-api.md                  # Account API
    ├── connection-api.md               # Connection API
    ├── audit-api.md                    # Audit API
    ├── metadata-api.md                 # Metadata API
    └── sql-api.md                      # SQL API
```

### 5.1 ドキュメントの更新方針

| ドキュメント | 更新タイミング |
|-------------|-------------|
| `product-requirements.md` | プロダクトの目的・機能要件が変わった場合 |
| `functional-design.md` | 画面構成・データモデル・API設計が変わった場合 |
| `architecture.md` | 技術スタック・システム構成が変わった場合 |
| `repository-structure.md` | フォルダ・ファイル構成が変わった場合 |
| `development-guidelines.md` | コーディング規約・開発フローが変わった場合 |
| `glossary.md` | 新しい用語・概念が登場した場合 |
| `api/` 配下 | Connect AI APIの仕様が更新された場合 |

---

## 6. .steering/

特定の開発作業における設計・タスクドキュメント。
作業ごとに新しいディレクトリを作成し、完了後も履歴として保持します。

```
.steering/
├── 20260217-initial-implementation/    # 初回実装（例）
│   ├── requirements.md                 # 今回の作業の要求内容
│   ├── design.md                       # 変更内容の設計
│   └── tasklist.md                     # タスクリストと進捗
└── 20260301-add-saved-queries/         # 保存クエリ機能追加（例）
    ├── requirements.md
    ├── design.md
    └── tasklist.md
```

### 6.1 命名規則

```
.steering/[YYYYMMDD]-[開発タイトル]/
```

- `YYYYMMDD`: 作業開始日付
- `開発タイトル`: 英小文字とハイフンのみ使用（例: `add-saved-queries`, `fix-auth-bug`）

---

## 7. ファイル配置ルール

### 7.1 新機能追加時の配置

新しい機能を追加する場合、以下の場所にファイルを配置します。

| 追加内容 | 配置先 |
|---------|-------|
| 新しいDBテーブル | `backend/models/` に新ファイル追加 |
| 新しいAPIエンドポイント群 | `backend/api/v1/` に新ファイル追加 + `backend/api/v1/__init__.py` に Blueprint登録 |
| 新しいビジネスロジック | `backend/services/` に新ファイル追加 |
| 新しい画面 | `frontend/pages/` にHTML追加 + `frontend/static/js/` にJS追加 |
| DBスキーマ変更 | `backend/migrations/versions/` にAlembicマイグレーションを自動生成 |

### 7.2 禁止事項

- `backend/api/v1/` にビジネスロジックを直接記述しない（必ずservicesに委譲）
- `frontend/pages/` にインラインのビジネスロジックを大量に記述しない（`static/js/` に分離）
- `docs/` 配下に実装コードを含めない
- `.env` ファイルをGitにコミットしない

### 7.3 .gitignore の対象

```
# 秘密情報
.env
private.key

# Python
__pycache__/
*.pyc
venv/
.venv/

# データベース
*.db
*.sqlite3

# OS
.DS_Store
Thumbs.db

# IDE
.vscode/settings.json
.idea/
```

---

## 8. 命名規則

### 8.1 ファイル名

| 種別 | 規則 | 例 |
|------|------|-----|
| Pythonファイル | スネークケース | `auth_service.py`, `connection_schema.py` |
| HTMLファイル | ケバブケース | `query-builder.html`, `data-browser.html` |
| JavaScriptファイル | ケバブケース | `api-client.js`, `query-builder.js` |
| CSSファイル | ケバブケース | `custom.css` |
| ドキュメント（Markdown） | ケバブケース | `functional-design.md`, `rest-api-basics.md` |

### 8.2 Pythonコード

| 種別 | 規則 | 例 |
|------|------|-----|
| クラス名 | パスカルケース | `AuthService`, `ConnectAIClient` |
| メソッド・関数名 | スネークケース | `register_user()`, `get_catalogs()` |
| 変数名 | スネークケース | `user_id`, `connect_ai_account_id` |
| 定数名 | 大文字スネークケース | `MAX_RETRY_COUNT`, `DEFAULT_TIMEOUT` |
| モジュール名 | スネークケース | `auth_service`, `connection_service` |

### 8.3 JavaScriptコード

| 種別 | 規則 | 例 |
|------|------|-----|
| クラス名 | パスカルケース | `APIClient`, `AuthManager` |
| メソッド・関数名 | キャメルケース | `executeQuery()`, `loadCatalogs()` |
| 変数名 | キャメルケース | `connectionId`, `jwtToken` |
| 定数名 | 大文字スネークケース | `API_BASE_URL`, `TOKEN_KEY` |

### 8.4 データベース・API

| 種別 | 規則 | 例 |
|------|------|-----|
| テーブル名 | スネークケース（複数形） | `users`, `connections`, `saved_queries` |
| カラム名 | スネークケース | `user_id`, `created_at`, `connect_ai_account_id` |
| APIエンドポイント | ケバブケース | `/api/v1/connections`, `/api/v1/query-builder` |
| JSONフィールド（リクエスト/レスポンス） | スネークケース | `data_source`, `redirect_url` |

---

**承認者**: _________________
**承認日**: _________________
