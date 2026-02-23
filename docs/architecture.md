# 技術仕様書: DataHub - Connect AI OEM リファレンス実装

**バージョン**: 1.1
**最終更新**: 2026-02-23

---

## 目次

1. [テクノロジースタック](#1-テクノロジースタック)
2. [システム構成](#2-システム構成)
3. [Connect AI API連携仕様](#3-connect-ai-api連携仕様)
4. [ローカル開発環境セットアップ](#4-ローカル開発環境セットアップ)
5. [依存ライブラリ](#5-依存ライブラリ)
6. [技術的制約と考慮事項](#6-技術的制約と考慮事項)

---

## 1. テクノロジースタック

### 1.1 Backend

| 技術 | バージョン | 用途 | 選定理由 |
|------|----------|------|---------|
| Python | 3.11+ | バックエンド言語 | 豊富なライブラリ、可読性の高いコード |
| Flask | 3.0.0 | Webフレームワーク | 軽量、シンプルな構成、デモ向け |
| Flask-Login | 0.6.3 | セッション管理 | Cookie ベースのユーザーセッション管理 |
| SQLAlchemy | 2.x | ORM | Python標準的なORM、SQLiteとPostgreSQLの両対応 |
| Alembic | 1.x | DBマイグレーション | SQLAlchemy公式のマイグレーションツール |
| Pydantic | 2.5.0 | データバリデーション | リクエスト/レスポンスのスキーマ検証 |
| email-validator | 2.1.0 | メールアドレス検証 | Pydantic の EmailStr 型に必要 |
| bcrypt | 4.1.2 | パスワードハッシュ化 | 業界標準のパスワードハッシュアルゴリズム |
| PyJWT | 2.8.0 | JWT生成・検証 | Connect AI用JWT（RS256）の生成 |
| cryptography | 41.0.7 | RSA署名 | Connect AI用JWT（RS256）の署名 |
| requests | 2.31.0 | HTTPクライアント | Connect AI APIへのHTTP呼び出し |
| python-dotenv | 1.0.0 | 環境変数管理 | .envファイルの読み込み |

### 1.2 Frontend

| 技術 | バージョン | 用途 | 選定理由 |
|------|----------|------|---------|
| HTML5 | - | マークアップ | 標準Web技術 |
| Tailwind CSS | 3.x | CSSフレームワーク | ユーティリティファースト、カスタマイズ容易 |
| Alpine.js | 3.x | リアクティブUI | 軽量（15KB）、Vanilla JSに近い学習コスト |
| Fetch API | - | HTTPクライアント | ブラウザ標準API、外部依存なし |

### 1.3 Database

| 技術 | 用途 | 備考 |
|------|------|------|
| SQLite 3 | 開発・デモ環境 | ファイルベース、セットアップ不要 |

### 1.4 Integration

| 技術 | 用途 |
|------|------|
| CData Connect AI Embedded Cloud | データソース接続・クエリ実行 |
| Connect AI Account API | ユーザー登録時の子アカウント作成 |
| Connect AI Connection API | コネクション作成・リダイレクト |
| Connect AI Metadata API | スキーマ・テーブル・カラム情報取得 |
| Connect AI SQL API | SQLクエリ実行（SELECT/INSERT/UPDATE/DELETE） |

---

## 2. システム構成

### 2.1 ローカル開発構成

```
┌───────────────────────────────────────┐
│         ローカル開発環境               │
│                                       │
│  ┌─────────────────────────────────┐  │
│  │       ブラウザ (Chrome等)       │  │
│  │  http://localhost:5001          │  │
│  └──────────────┬──────────────────┘  │
│                 │ HTTP                │
│  ┌──────────────▼──────────────────┐  │
│  │    Flask Dev Server             │  │
│  │    port: 5001                   │  │
│  │                                 │  │
│  │  ┌─────────────────────────┐   │  │
│  │  │  Frontend (HTML/JS)     │   │  │
│  │  │  /frontend/             │   │  │
│  │  └─────────────────────────┘   │  │
│  │  ┌─────────────────────────┐   │  │
│  │  │  Backend API            │   │  │
│  │  │  /backend/              │   │  │
│  │  └──────────┬──────────────┘   │  │
│  └─────────────┼───────────────────┘  │
│                │                      │
│  ┌─────────────▼───────────────────┐  │
│  │    SQLite DB                    │  │
│  │    datahub.db                   │  │
│  └─────────────────────────────────┘  │
└───────────────────┬───────────────────┘
                    │ HTTPS
          ┌─────────▼─────────┐
          │  CData Connect AI  │
          │  Embedded Cloud    │
          │  (External API)    │
          └───────────────────┘
```

### 2.2 ディレクトリ構造

```
ConnectAIOEMSample/
├── backend/
│   ├── app.py                    # Flaskアプリ・ルーティング設定
│   ├── config.py                 # 環境設定（パス解決含む）
│   ├── models/
│   │   ├── __init__.py           # DB初期化
│   │   ├── user.py               # Userモデル
│   │   └── api_log.py            # ApiLogモデル
│   ├── schemas/
│   │   ├── user_schema.py        # ユーザー登録・ログインのスキーマ
│   │   ├── connection_schema.py  # コネクション作成のスキーマ
│   │   ├── query_schema.py       # クエリ実行のスキーマ
│   │   └── data_schema.py        # データCRUDのスキーマ
│   ├── services/
│   │   ├── auth_service.py       # 認証・Connect AI Account API
│   │   ├── connection_service.py # コネクション管理・Connection API
│   │   ├── metadata_service.py   # Metadata API呼び出し
│   │   ├── query_service.py      # SQL API呼び出し
│   │   ├── data_service.py       # データCRUD操作
│   │   └── api_log_service.py    # API ログ取得
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py           # POST /api/v1/auth/*
│   │       ├── connections.py    # /api/v1/connections/*
│   │       ├── metadata.py       # GET /api/v1/metadata/*
│   │       ├── query.py          # POST /api/v1/query/*
│   │       ├── data.py           # /api/v1/data/*
│   │       └── api_log.py        # GET /api/v1/api-logs
│   ├── connectai/
│   │   ├── client.py             # Connect AI HTTP APIクライアント
│   │   ├── jwt.py                # Connect AI用JWT生成（RS256）
│   │   └── exceptions.py        # Connect AI固有の例外クラス
│   ├── middleware/
│   │   └── error_handler.py      # グローバルエラーハンドラー
│   ├── keys/
│   │   ├── private.key           # RSA秘密鍵（gitignore対象）
│   │   └── public.key            # RSA公開鍵（gitignore対象）
│   ├── tests/
│   │   ├── conftest.py           # pytestの共通フィクスチャ
│   │   ├── test_auth.py
│   │   ├── test_connections.py
│   │   ├── test_metadata.py
│   │   ├── test_query.py
│   │   ├── test_data.py
│   │   └── test_api_log.py
│   ├── requirements.txt
│   └── .env                      # 環境変数（gitignore対象）
├── frontend/
│   ├── pages/
│   │   ├── login.html
│   │   ├── register.html
│   │   ├── dashboard.html
│   │   ├── connections.html
│   │   ├── connections-new.html
│   │   ├── callback.html
│   │   ├── explorer.html
│   │   ├── query.html
│   │   ├── data-browser.html
│   │   └── api-log.html
│   └── static/
│       └── js/
│           ├── api-client.js     # バックエンドAPIとの通信クラス
│           ├── auth.js           # ログアウト処理
│           └── header.js         # 共通ヘッダーコンポーネント
├── migrations/                   # Alembicマイグレーション（プロジェクトルート）
│   ├── alembic.ini
│   ├── env.py
│   └── versions/
├── docs/
├── .steering/
├── .gitignore
└── README.md
```

### 2.3 リクエストの流れ

#### フロントエンドのホスティング

Flaskが静的ファイル（HTML/JS）とAPIの両方を同一ポートで提供します。

```python
# app.py
app = Flask(__name__, static_folder='../frontend/static', template_folder='../frontend/pages')

@app.route('/')
def index():
    return redirect('/login')

@app.route('/login')
def login_page():
    return render_template('login.html')
```

#### APIリクエストのフロー

```
Browser → GET http://localhost:5001/dashboard
        ← HTML (dashboard.html)

Browser → GET http://localhost:5001/static/js/api-client.js
        ← JavaScript

Browser → POST http://localhost:5001/api/v1/metadata/tables
          (Cookie: session=...)
        ← JSON { tables: [...] }
```

---

## 3. Connect AI API連携仕様

### 3.1 認証方式

Connect AI APIへのすべてのリクエストに **RS256 JWT** を使用します。

#### JWTの生成

```python
# backend/connectai/jwt.py
import time
import jwt
from cryptography.hazmat.primitives import serialization
from flask import current_app

def generate_connect_ai_jwt(parent_account_id: str, subject_account_id: str) -> str:
    """
    Connect AI API 用 RS256 JWT を生成する。

    Args:
        parent_account_id: ParentAccountId（iss クレーム）
        subject_account_id: 呼び出し対象アカウントID（sub クレーム）
                            子アカウント未作成時は空文字列にする
    Returns:
        署名済み JWT 文字列
    """
    private_key_path = current_app.config["CONNECT_AI_PRIVATE_KEY_PATH"]
    with open(private_key_path, "rb") as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None)

    now = int(time.time())
    payload = {
        "tokenType": "powered-by",
        "iss": parent_account_id,
        "sub": subject_account_id,
        "iat": now,
        "exp": now + 3600,
    }
    return jwt.encode(payload, private_key, algorithm="RS256")
```

#### 環境変数

| 変数名 | 説明 | 例 |
|-------|------|-----|
| `CONNECT_AI_BASE_URL` | Connect AI APIのベースURL | `https://cloud.cdata.com/api` |
| `CONNECT_AI_PARENT_ACCOUNT_ID` | 親アカウントID | `abc-123-def` |
| `CONNECT_AI_PRIVATE_KEY_PATH` | RSA秘密鍵ファイルパス（相対または絶対パス） | `backend/keys/private.key` |

> **注意**: 旧設計では秘密鍵のPEM文字列を環境変数に直接設定していましたが、現在の実装ではファイルパスを指定します。`config.py` が相対パスを自動的にプロジェクトルートからの絶対パスに変換します。

### 3.2 APIクライアント

```python
# backend/connectai/client.py
class ConnectAIClient:
    """
    Connect AI HTTP API クライアント。
    各メソッド呼び出し時に JWT を生成してリクエストに付与する。
    """

    def __init__(self, child_account_id: str | None):
        self.base_url = current_app.config["CONNECT_AI_BASE_URL"]
        self.parent_account_id = current_app.config["CONNECT_AI_PARENT_ACCOUNT_ID"]
        # 子アカウント未作成の場合は空文字列を使う（Account API 呼び出し時）
        self.subject_id = child_account_id if child_account_id is not None else ""

    def _headers(self) -> dict:
        token = generate_connect_ai_jwt(self.parent_account_id, self.subject_id)
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
```

### 3.3 利用するAPIエンドポイント一覧

| API | エンドポイント | 利用タイミング |
|-----|--------------|--------------|
| Account API | `POST /poweredby/account/create` | ユーザー登録時 |
| Connection API | `GET /poweredby/sources/list` | コネクション作成画面 |
| Connection API | `GET /poweredby/connection/list` | コネクション一覧表示時 |
| Connection API | `POST /poweredby/connection/create` | コネクション作成時 |
| Connection API | `DELETE /poweredby/connection/delete/{id}` | コネクション削除時 |
| Metadata API | `GET /catalogs` | メタデータエクスプローラー |
| Metadata API | `GET /schemas` | メタデータエクスプローラー |
| Metadata API | `GET /tables` | メタデータエクスプローラー・クエリビルダー |
| Metadata API | `GET /columns` | メタデータエクスプローラー・データブラウザ |
| SQL API | `POST /query` | クエリビルダー・データブラウザ（SELECT/INSERT/UPDATE/DELETE） |

---

## 4. ローカル開発環境セットアップ

### 4.1 前提条件

- Python 3.11 以上
- pip
- Git
- CData Connect AI アカウント（親アカウント）とRSA鍵ペア

### 4.2 セットアップ手順

```bash
# 1. リポジトリのクローン
git clone <repository_url>
cd ConnectAIOEMSample

# 2. Python仮想環境の作成・有効化
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. 依存パッケージのインストール
pip install -r backend/requirements.txt

# 4. 環境変数の設定
# backend/.env を編集して各変数を設定

# 5. RSA鍵ペアの生成（初回のみ）
openssl genrsa -out backend/keys/private.key 4096
openssl rsa -in backend/keys/private.key -pubout -out backend/keys/public.key
# public.key の内容を CData サポートチームに登録する

# 6. データベースの初期化
PYTHONPATH=$(pwd) flask --app backend.app db upgrade

# 7. 開発サーバーの起動
PYTHONPATH=$(pwd) flask --app backend.app run --port 5001 --debug
# → http://localhost:5001 でアクセス可能
```

### 4.3 環境変数一覧（backend/.env）

```bash
# アプリケーション設定
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=change-me-to-a-random-string  # Cookie署名用シークレットキー

# データベース
DATABASE_URL=sqlite:///datahub.db

# CData Connect AI設定
CONNECT_AI_BASE_URL=https://cloud.cdata.com/api
CONNECT_AI_PARENT_ACCOUNT_ID=your-parent-account-id

# RSA秘密鍵ファイルパス（プロジェクトルートからの相対パス、または絶対パス）
CONNECT_AI_PRIVATE_KEY_PATH=backend/keys/private.key

# コールバックURL（コネクション作成後のリダイレクト先）
APP_BASE_URL=http://localhost:5001
```

### 4.4 RSA鍵ペアの生成

```bash
# 秘密鍵の生成（4096ビット）
openssl genrsa -out backend/keys/private.key 4096

# 公開鍵の生成
openssl rsa -in backend/keys/private.key -pubout -out backend/keys/public.key
```

生成した公開鍵（`public.key`の内容）をCDataサポートチームに登録します。秘密鍵（`private.key`）は `backend/keys/private.key` に配置し、`.gitignore` により Git管理対象外となります。

---

## 5. 依存ライブラリ

### 5.1 backend/requirements.txt

```text
# Webフレームワーク
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-Migrate==4.0.5
Flask-Login==0.6.3

# データバリデーション
pydantic==2.5.0
email-validator==2.1.0

# 認証・暗号化
bcrypt==4.1.2
PyJWT==2.8.0
cryptography==41.0.7

# HTTPクライアント
requests==2.31.0

# 環境変数
python-dotenv==1.0.0

# テスト
pytest==7.4.3
pytest-cov==4.1.0
```

> **注**: pytest はテスト用ですが `requirements.txt` に含まれています（`requirements-dev.txt` は存在しません）。

### 5.2 フロントエンド（CDN経由で読み込み）

```html
<!-- Tailwind CSS -->
<script src="https://cdn.tailwindcss.com"></script>

<!-- Alpine.js -->
<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
```

---

## 6. 技術的制約と考慮事項

### 6.1 Connect AI APIの制約

| 制約 | 内容 |
|------|------|
| JWT有効期限 | 最長1時間（リクエストごとに新規生成を推奨） |
| タイムアウト | SQL APIのタイムアウト最大300秒（クライアント側は30秒に設定） |
| コネクション作成 | `redirectURL`は必須。ローカル開発では`http://localhost:5001/callback`を使用 |

### 6.2 ローカル開発の制約

| 制約 | 内容 |
|------|------|
| HTTPSなし | ローカル開発ではHTTP。本番移行時はHTTPS対応が必要 |
| シングルプロセス | FlaskのDev ServerはシングルスレッドのためConcurrentリクエストに非対応 |
| SQLite | マルチプロセス書き込みに非対応。デモ用途のみ使用 |

### 6.3 セキュリティに関する注意事項

- `SECRET_KEY` と `CONNECT_AI_PRIVATE_KEY_PATH` 配下の秘密鍵はGitにコミットしないこと（`.gitignore` に設定済み）
- デモ環境であっても、RSA秘密鍵は厳重に管理すること
- ユーザー入力をSQL文に直接埋め込まず、必ずConnect AI APIの`parameters`オプションを使用すること

### 6.4 認証方式について

本アプリケーションは **Flask-Login による Cookie ベースのセッション管理** を採用しています。

- ログイン成功時に Flask-Login がセッション Cookie を発行
- 以降のリクエストは Cookie により認証済みユーザーを識別
- **JWT をフロントエンドの localStorage に保存する方式は採用していません**

### 6.5 コネクション管理について

コネクション情報（接続先・認証情報）は **Connect AI 側で管理** されます。

- アプリケーション側の DB には `Connection` モデルは存在しません
- コネクション一覧は `GET /poweredby/connection/list` API で取得します
- アプリ側は `User` モデルの `connect_ai_account_id` を通じてテナント分離を実現します

### 6.6 データソースの`name`について

Connect AI Connection APIの`name`パラメータに指定した値が、その後のMetadata/SQL APIで`catalogName`として使用されます。コネクション名は英数字とハイフン・アンダースコアのみ使用することを推奨します（スペースや特殊文字を避ける）。

---

**承認者**: _________________
**承認日**: _________________
