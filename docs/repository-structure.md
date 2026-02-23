# リポジトリ構造定義書: DataHub - Connect AI OEM リファレンス実装

**バージョン**: 1.2
**最終更新**: 2026-02-23

---

## 目次

1. [全体構成](#1-全体構成)
2. [ルートディレクトリ](#2-ルートディレクトリ)
3. [backend/](#3-backend)
4. [frontend/](#4-frontend)
5. [migrations/](#5-migrations)
6. [docs/](#6-docs)
7. [.steering/](#7-steering)
8. [ファイル配置ルール](#8-ファイル配置ルール)
9. [命名規則](#9-命名規則)

---

## 1. 全体構成

```
ConnectAIOEMSample/                     # リポジトリルート
├── backend/                            # Pythonバックエンド
├── frontend/                           # HTML/JSフロントエンド
├── migrations/                         # Alembicマイグレーション
├── docs/                               # 永続的ドキュメント
├── .steering/                          # 作業単位のドキュメント
├── .gitignore                          # Git除外設定
├── CLAUDE.md                           # AI開発ガイド（プロジェクトメモリ）
└── README.md                           # プロジェクト説明
```

---

## 2. ルートディレクトリ

| ファイル/ディレクトリ | 役割 | コミット |
|----------------------|------|---------|
| `backend/` | Flaskアプリケーション本体 | ✓ |
| `frontend/` | HTML/JSファイル群 | ✓ |
| `migrations/` | Alembicマイグレーションスクリプト | ✓ |
| `docs/` | 永続的なプロジェクトドキュメント | ✓ |
| `.steering/` | 作業単位の設計・タスクドキュメント | ✓ |
| `.gitignore` | Git管理対象外の定義 | ✓ |
| `CLAUDE.md` | Claude Code向け開発ガイドライン | ✓ |
| `README.md` | セットアップ手順、プロジェクト概要 | ✓ |

---

## 3. backend/

Flaskアプリケーションのすべてのコードを格納します。

```
backend/
├── app.py                              # アプリケーションエントリーポイント
├── config.py                           # 環境別設定クラス（パス解決含む）
├── models/                             # SQLAlchemyモデル
│   ├── __init__.py                     # DBインスタンス生成・モデルのエクスポート
│   ├── user.py                         # Userモデル
│   └── api_log.py                      # ApiLogモデル（Phase 3）
├── schemas/                            # Pydanticスキーマ（リクエスト/レスポンス検証）
│   ├── __init__.py
│   ├── user_schema.py                  # ユーザー登録・ログインのスキーマ
│   ├── connection_schema.py            # コネクション作成のスキーマ
│   ├── query_schema.py                 # クエリ実行のスキーマ
│   └── data_schema.py                  # データCRUDのスキーマ
├── services/                           # ビジネスロジック層
│   ├── __init__.py
│   ├── auth_service.py                 # 認証・Connect AI Account API
│   ├── connection_service.py           # コネクション管理・Connection API
│   ├── metadata_service.py             # Metadata API呼び出し
│   ├── query_service.py                # SQL API呼び出し（クエリ実行）
│   ├── data_service.py                 # データCRUD操作
│   ├── api_log_service.py              # API ログ取得
│   ├── crypto_service.py               # Fernet暗号化ユーティリティ（Phase 4）
│   ├── mcp_client.py                   # Connect AI MCP Streamable HTTP クライアント（Phase 4）
│   └── claude_service.py               # Claude API + Agentic loop + SSE（Phase 4）
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
│       ├── query.py                    # POST /api/v1/query/*
│       ├── data.py                     # /api/v1/data/*
│       ├── api_log.py                  # GET/DELETE /api/v1/api-logs
│       ├── settings.py                 # GET|POST|DELETE /api/v1/settings/api-key（Phase 4）
│       └── ai_assistant.py             # GET|POST /api/v1/ai-assistant/*（Phase 4）
├── middleware/                         # リクエスト前処理
│   ├── __init__.py
│   └── error_handler.py                # グローバルエラーハンドラー
├── keys/                               # RSA鍵ペア格納ディレクトリ
│   ├── private.key                     # RSA秘密鍵（gitignore対象）
│   ├── public.key                      # RSA公開鍵（gitignore対象）
│   └── README.md                       # 鍵管理手順
├── tests/                              # ユニット・インテグレーションテスト
│   ├── __init__.py
│   ├── conftest.py                     # pytestの共通フィクスチャ
│   ├── test_auth.py                    # 認証APIのテスト
│   ├── test_connections.py             # コネクションAPIのテスト
│   ├── test_metadata.py                # メタデータAPIのテスト
│   ├── test_query.py                   # クエリAPIのテスト
│   ├── test_data.py                    # データCRUD APIのテスト
│   └── test_api_log.py                 # API ログAPIのテスト（Phase 3）
├── requirements.txt                    # 依存パッケージ（pytest含む）
└── .env                                # 環境変数（gitignore対象）
```

### 3.1 各ディレクトリの役割

#### backend/app.py
- Flaskアプリケーションの生成・初期化
- Blueprintの登録
- フロントエンドの静的ファイル・HTMLテンプレートの提供
- Flask-Login の初期化

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
- `_PROJECT_ROOT = Path(__file__).resolve().parent.parent` でプロジェクトルートを特定
- `_resolve_path()` で `CONNECT_AI_PRIVATE_KEY_PATH` を絶対パスに変換（起動ディレクトリに依存しない）

#### backend/models/
- SQLAlchemyモデルクラスを1ファイルにつき1モデルで定義
- `__init__.py` で `db = SQLAlchemy()` インスタンスを生成し、各モデルをインポート
- **注意**: `Connection` モデルは存在しません（コネクション情報はConnect AI側で管理）

#### backend/schemas/
- Pydanticモデルによるリクエスト/レスポンスのバリデーション
- APIエンドポイントでの入力検証に使用

#### backend/services/
- ビジネスロジックをAPIルーティングから分離
- データベース操作・外部API呼び出しを担当
- Blueprintから直接データベースやAPIを操作しない（serviceを経由する）

#### backend/connectai/
- CData Connect AI APIとの通信を担当するモジュール
- `client.py`: HTTP APIクライアント（`requests`ライブラリを使用）。全 API 呼び出し結果を非同期で `ApiLog` に記録
- `jwt.py`: RS256署名のJWTトークン生成（秘密鍵ファイルを読み込み）
- `exceptions.py`: APIエラーを表すカスタム例外

#### backend/api/v1/
- Flaskの `Blueprint` を使用したエンドポイント定義
- HTTP層のみ（リクエスト/レスポンスの処理）。ビジネスロジックはservices/に委譲

#### backend/middleware/
- `error_handler.py`: 未処理の例外をJSONエラーレスポンスに変換

#### backend/keys/
- RSA鍵ペアの格納ディレクトリ
- `private.key`、`public.key` はいずれも `.gitignore` により Git 管理対象外

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
│   ├── connections-new.html            # コネクション作成画面
│   ├── callback.html                   # コネクション認証コールバック画面
│   ├── explorer.html                   # メタデータエクスプローラー
│   ├── query.html                      # クエリビルダー
│   ├── data-browser.html               # データブラウザ（CRUD）
│   ├── api-log.html                    # API ログ閲覧画面（Phase 3）
│   ├── settings.html                   # Claude API Key 設定画面（Phase 4）
│   └── ai-assistant.html               # AI アシスタントチャット画面（Phase 4）
└── static/                             # 静的ファイル（/static/ でアクセス可能）
    └── js/
        ├── api-client.js               # バックエンドAPIとの通信クラス
        ├── auth.js                     # ログアウト処理（logout() 関数定義）
        └── header.js                   # 共通ヘッダーコンポーネント（Phase 3）
```

### 4.1 各ファイルの役割

#### frontend/pages/
- 各画面のHTMLファイル
- Tailwind CSS・Alpine.jsはCDN経由で読み込む（ビルド不要）
- Alpine.jsのリアクティブ状態はHTMLインライン（`x-data`）で管理
- 保護ページは `<head>` 内で `header.js` を読み込み、`renderAppHeader('page-id')` を呼び出す

#### frontend/static/js/
- **`api-client.js`**: 全ページで共通使用する `APIClient` クラス。Cookie セッション認証前提
- **`auth.js`**: `logout()` グローバル関数を定義。全保護ページで読み込む
- **`header.js`**: `renderAppHeader(currentPage)` グローバル関数を定義。Alpine.js の defer より前に同期読み込みする

> **注意**: CSS ファイル（`custom.css`）、画像ファイル（`logo.svg`）、ページ個別の JS ファイルは存在しません。スタイルはすべて Tailwind CSS ユーティリティクラスで記述しています。

---

## 5. migrations/

Alembicマイグレーションスクリプトを格納します。**プロジェクトルートに配置します**（`backend/` 内ではありません）。

```
migrations/
├── alembic.ini                         # Alembic設定
├── env.py                              # マイグレーション実行環境設定
└── versions/                           # マイグレーションスクリプト
    └── *.py                            # 各バージョンのスクリプト
```

**マイグレーション実行コマンド:**
```bash
# プロジェクトルートから実行
PYTHONPATH=$(pwd) flask --app backend.app db upgrade
PYTHONPATH=$(pwd) flask --app backend.app db migrate -m "migration name"
```

---

## 6. docs/

アプリケーション全体の設計を定義する永続的なドキュメント。

```
docs/
├── product-requirements.md             # プロダクト要求定義書
├── functional-design.md                # 機能設計書
├── architecture.md                     # 技術仕様書
├── repository-structure.md             # リポジトリ構造定義書（本ドキュメント）
├── development-guidelines.md           # 開発ガイドライン
├── glossary.md                         # ユビキタス言語定義
└── api/                                # Connect AI API リファレンス
    ├── README.md                       # API ドキュメント目次
    ├── overview.md                     # API 概要
    ├── authentication.md               # 認証仕様
    ├── rest-api-basics.md              # REST API 基本仕様
    ├── account-api.md                  # アカウント API
    ├── connection-api.md               # コネクション API
    ├── audit-api.md                    # 監査 API
    ├── metadata-api.md                 # メタデータ API
    ├── sql-api.md                      # SQL API
    └── mcp-api.md                      # MCP API（Streamable HTTP）Phase 4
```

### 6.1 ドキュメントの更新方針

| ドキュメント | 更新タイミング |
|-------------|-------------|
| `product-requirements.md` | プロダクトの目的・機能要件が変わった場合 |
| `functional-design.md` | 画面構成・データモデル・API設計が変わった場合 |
| `architecture.md` | 技術スタック・システム構成が変わった場合 |
| `repository-structure.md` | フォルダ・ファイル構成が変わった場合 |
| `development-guidelines.md` | コーディング規約・開発フローが変わった場合 |
| `glossary.md` | 新しい用語・概念が登場した場合 |

---

## 7. .steering/

特定の開発作業における設計・タスクドキュメント。
作業ごとに新しいディレクトリを作成し、完了後も履歴として保持します。

```
.steering/
├── 20260222-phase1-01-auth/            # Phase 1-01: 認証機能
│   ├── requirements.md
│   ├── design.md
│   └── tasklist.md
├── 20260222-phase1-02-connections/     # Phase 1-02: コネクション管理
│   ├── requirements.md
│   ├── design.md
│   └── tasklist.md
├── 20260223-phase1-03-metadata-explorer/ # Phase 1-03: メタデータエクスプローラー
│   ├── requirements.md
│   ├── design.md
│   └── tasklist.md
├── 20260223-phase2-01-query-builder/   # Phase 2-01: クエリビルダー
│   ├── requirements.md
│   ├── design.md
│   └── tasklist.md
├── 20260223-phase2-02-crud/            # Phase 2-02: データCRUD操作
│   ├── requirements.md
│   ├── design.md
│   └── tasklist.md
├── 20260223-phase3-01-api-log/         # Phase 3-01: API ログ
│   ├── requirements.md
│   ├── design.md
│   └── tasklist.md
├── 20260223-ai-assistant/              # Phase 4: AI アシスタント（共通ドキュメント・インデックス）
│   ├── requirements.md
│   ├── design.md
│   └── tasklist.md                     # フェーズ一覧インデックス
├── 20260223-phase4-01-infrastructure/  # Phase 4-01: 基盤整備（API Key 管理）
│   └── tasklist.md
├── 20260223-phase4-02-mcp-client/      # Phase 4-02: MCP クライアント
│   └── tasklist.md
├── 20260223-phase4-03-chat-basic/      # Phase 4-03: チャット基本動作
│   └── tasklist.md
├── 20260223-phase4-04-streaming/       # Phase 4-04: SSE ストリーミング
│   └── tasklist.md
├── 20260223-phase4-05-tool-visibility/ # Phase 4-05: MCP ツール呼び出し可視化
│   └── tasklist.md
└── 20260223-phase4-06-conversation/    # Phase 4-06: 会話コンテキスト保持
    └── tasklist.md
```

### 7.1 命名規則

```
.steering/[YYYYMMDD]-[開発タイトル]/
```

- `YYYYMMDD`: 作業開始日付
- `開発タイトル`: 英小文字とハイフンのみ使用（例: `add-api-log`, `fix-auth-bug`）

---

## 8. ファイル配置ルール

### 8.1 新機能追加時の配置

新しい機能を追加する場合、以下の場所にファイルを配置します。

| 追加内容 | 配置先 |
|---------|-------|
| 新しいDBテーブル | `backend/models/` に新ファイル追加 |
| 新しいAPIエンドポイント群 | `backend/api/v1/` に新ファイル追加 + `backend/api/v1/__init__.py` に Blueprint登録 |
| 新しいビジネスロジック | `backend/services/` に新ファイル追加 |
| 新しいリクエスト/レスポンスのスキーマ | `backend/schemas/` に新ファイル追加 |
| 新しい画面 | `frontend/pages/` にHTML追加 |
| DBスキーマ変更 | `flask db migrate` でマイグレーションを自動生成（プロジェクトルートから実行） |
| Claude API Key の保存 | `backend/services/crypto_service.py` の Fernet 暗号化を必ず使用する |
| MCP 呼び出し | `backend/services/mcp_client.py` を経由する（API ルートから直接 HTTP リクエストしない） |

### 8.2 禁止事項

- `backend/api/v1/` にビジネスロジックを直接記述しない（必ずservicesに委譲）
- `frontend/pages/` にページ個別の大量なビジネスロジックJSファイルを作成しない（Alpine.jsインラインで管理）
- `docs/` 配下に実装コードを含めない
- `backend/.env` ファイルをGitにコミットしない
- `backend/keys/private.key`、`backend/keys/public.key` をGitにコミットしない

### 8.3 .gitignore の対象

```
# 秘密情報
backend/.env
backend/keys/private.key
backend/keys/public.key
backend/keys/parent_account_id.txt

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

## 9. 命名規則

### 9.1 ファイル名

| 種別 | 規則 | 例 |
|------|------|-----|
| Pythonファイル | スネークケース | `auth_service.py`, `api_log.py` |
| HTMLファイル | ケバブケース | `api-log.html`, `data-browser.html` |
| JavaScriptファイル | ケバブケース | `api-client.js`, `header.js` |
| ドキュメント（Markdown） | ケバブケース | `functional-design.md` |

### 9.2 Pythonコード

| 種別 | 規則 | 例 |
|------|------|-----|
| クラス名 | パスカルケース | `AuthService`, `ConnectAIClient` |
| メソッド・関数名 | スネークケース | `register_user()`, `get_catalogs()` |
| 変数名 | スネークケース | `user_id`, `connect_ai_account_id` |
| 定数名 | 大文字スネークケース | `_TYPE_NAME_TO_DATA_TYPE` |
| モジュール名 | スネークケース | `auth_service`, `api_log_service` |

### 9.3 JavaScriptコード

| 種別 | 規則 | 例 |
|------|------|-----|
| クラス名 | パスカルケース | `APIClient` |
| メソッド・関数名 | キャメルケース | `executeQuery()`, `renderAppHeader()` |
| 変数名 | キャメルケース | `connectionId`, `currentPage` |

### 9.4 データベース・API

| 種別 | 規則 | 例 |
|------|------|-----|
| テーブル名 | スネークケース（複数形） | `users`, `api_logs` |
| カラム名 | スネークケース | `user_id`, `created_at`, `connect_ai_account_id` |
| APIエンドポイント | ケバブケース | `/api/v1/connections`, `/api/v1/api-logs` |
| JSONフィールド（リクエスト/レスポンス） | スネークケース | `data_source`, `redirect_url` |

---

**承認者**: _________________
**承認日**: _________________
