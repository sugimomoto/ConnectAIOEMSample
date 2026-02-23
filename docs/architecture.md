# 技術仕様書: DataHub - Connect AI OEM リファレンス実装

**バージョン**: 1.0
**最終更新**: 2026-02-17

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
| Flask | 3.x | Webフレームワーク | 軽量、シンプルな構成、デモ向け |
| SQLAlchemy | 2.x | ORM | Python標準的なORM、SQLiteとPostgreSQLの両対応 |
| Alembic | 1.x | DBマイグレーション | SQLAlchemy公式のマイグレーションツール |
| Pydantic | 2.x | データバリデーション | リクエスト/レスポンスのスキーマ検証 |
| bcrypt | 4.x | パスワードハッシュ化 | 業界標準のパスワードハッシュアルゴリズム |
| PyJWT | 2.x | JWT生成・検証 | アプリケーション用JWT |
| cryptography | 41.x | RSA署名 | Connect AI用JWT（RS256）の署名 |
| requests | 2.x | HTTPクライアント | Connect AI APIへのHTTP呼び出し |
| python-dotenv | 1.x | 環境変数管理 | .envファイルの読み込み |

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
│  │  http://localhost:5000          │  │
│  └──────────────┬──────────────────┘  │
│                 │ HTTP                │
│  ┌──────────────▼──────────────────┐  │
│  │    Flask Dev Server             │  │
│  │    port: 5000                   │  │
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
│   ├── config.py                 # 環境設定（開発/本番）
│   ├── models/
│   │   ├── __init__.py           # DB初期化
│   │   ├── user.py               # Userモデル
│   │   └── connection.py         # Connectionモデル
│   ├── services/
│   │   ├── auth_service.py       # 認証・Connect AI Account API
│   │   ├── connection_service.py # コネクション管理・Connection API
│   │   ├── metadata_service.py   # Metadata API呼び出し
│   │   └── query_service.py      # SQL API呼び出し
│   ├── api/
│   │   ├── auth.py               # POST /api/v1/auth/*
│   │   ├── connections.py        # /api/v1/connections/*
│   │   ├── metadata.py           # GET /api/v1/metadata/*
│   │   └── queries.py            # POST /api/v1/queries/*
│   ├── connectai/
│   │   ├── client.py             # Connect AI APIクライアント
│   │   └── jwt.py                # Connect AI用JWT生成（RS256）
│   ├── middleware/
│   │   └── auth.py               # JWT検証デコレータ
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── pages/
│   │   ├── login.html
│   │   ├── register.html
│   │   ├── dashboard.html
│   │   ├── connections.html
│   │   ├── explorer.html
│   │   ├── query-builder.html
│   │   └── data-browser.html
│   └── static/
│       ├── css/
│       │   └── tailwind.css
│       └── js/
│           ├── api-client.js
│           ├── auth.js
│           └── utils.js
├── docs/
├── .env.example
├── .gitignore
└── README.md
```

### 2.3 リクエストの流れ

#### フロントエンドのホスティング

Flaskが静的ファイル（HTML/CSS/JS）とAPIの両方を同一ポートで提供します。

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
Browser → GET http://localhost:5000/dashboard
        ← HTML (dashboard.html)

Browser → GET http://localhost:5000/static/js/api-client.js
        ← JavaScript

Browser → POST http://localhost:5000/api/v1/metadata/tables
          Authorization: Bearer {JWT}
        ← JSON { tables: [...] }
```

---

## 3. Connect AI API連携仕様

### 3.1 認証方式

Connect AI APIへのすべてのリクエストに **RS256 JWT** を使用します。

#### JWTの生成

```python
# backend/connectai/jwt.py
import jwt
import time
from cryptography.hazmat.primitives import serialization

def generate_connect_ai_jwt(
    parent_account_id: str,
    child_account_id: str,
    private_key_pem: str,
    expires_in: int = 3600
) -> str:
    """
    Connect AI API用のJWTトークンを生成する

    Args:
        parent_account_id: 親アカウントID（環境変数から取得）
        child_account_id: 子アカウントID（users.connect_ai_account_id）
        private_key_pem: RSA秘密鍵（PEM形式、環境変数から取得）
        expires_in: 有効期限（秒）

    Returns:
        JWT Token文字列
    """
    now = int(time.time())
    payload = {
        "tokenType": "powered-by",
        "iat": now,
        "exp": now + expires_in,
        "iss": parent_account_id,
        "sub": child_account_id,
    }
    private_key = serialization.load_pem_private_key(
        private_key_pem.encode(), password=None
    )
    return jwt.encode(payload, private_key, algorithm="RS256")
```

#### 環境変数

| 変数名 | 説明 | 例 |
|-------|------|-----|
| `CONNECT_AI_BASE_URL` | Connect AI APIのベースURL | `https://cloud.cdata.com/api` |
| `CONNECT_AI_PARENT_ACCOUNT_ID` | 親アカウントID | `abc-123-def` |
| `CONNECT_AI_PRIVATE_KEY` | RSA秘密鍵（PEM形式、改行は`\n`） | `-----BEGIN RSA PRIVATE KEY-----\n...` |

### 3.2 APIクライアント

```python
# backend/connectai/client.py
import requests
from .jwt import generate_connect_ai_jwt

class ConnectAIClient:
    """
    CData Connect AI APIのHTTPクライアント

    各インスタンスはユーザーの子アカウント（account_id）に紐付き、
    APIコールごとにJWTを生成してAuthorizationヘッダーに付与する
    """

    def __init__(self, account_id: str):
        self.base_url = os.getenv("CONNECT_AI_BASE_URL")
        self.account_id = account_id

    def _get_headers(self) -> dict:
        token = generate_connect_ai_jwt(
            parent_account_id=os.getenv("CONNECT_AI_PARENT_ACCOUNT_ID"),
            child_account_id=self.account_id,
            private_key_pem=os.getenv("CONNECT_AI_PRIVATE_KEY"),
        )
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def _request(self, method: str, path: str, **kwargs) -> dict:
        url = f"{self.base_url}{path}"
        resp = requests.request(method, url, headers=self._get_headers(), **kwargs)
        resp.raise_for_status()
        return resp.json()
```

### 3.3 利用するAPIエンドポイント一覧

| API | エンドポイント | 利用タイミング |
|-----|--------------|--------------|
| Account API | `POST /poweredby/account/create` | ユーザー登録時 |
| Connection API | `POST /poweredby/connection/create` | コネクション作成時 |
| Metadata API | `GET /catalogs` | メタデータエクスプローラー |
| Metadata API | `GET /schemas` | メタデータエクスプローラー |
| Metadata API | `GET /tables` | メタデータエクスプローラー・クエリビルダー |
| Metadata API | `GET /columns` | メタデータエクスプローラー・フォーム自動生成 |
| SQL API | `POST /query` | クエリビルダー・データブラウザ（SELECT） |
| SQL API | `POST /query` | データブラウザ（INSERT/UPDATE/DELETE） |
| SQL API | `POST /batch` | データブラウザ（バッチ操作） |

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
cp .env.example .env
# .envを編集して各変数を設定

# 5. データベースの初期化
cd backend
flask db upgrade

# 6. 開発サーバーの起動
flask run --debug
# → http://localhost:5000 でアクセス可能
```

### 4.3 環境変数一覧（.env）

```bash
# アプリケーション設定
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=your-secret-key-here           # JWT署名用シークレットキー（任意の文字列）

# データベース
DATABASE_URL=sqlite:///datahub.db

# CData Connect AI設定
CONNECT_AI_BASE_URL=https://cloud.cdata.com/api
CONNECT_AI_PARENT_ACCOUNT_ID=your-parent-account-id
CONNECT_AI_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----"

# コールバックURL（コネクション作成後のリダイレクト先）
APP_BASE_URL=http://localhost:5000
```

### 4.4 RSA鍵ペアの生成

```bash
# 秘密鍵の生成（4096ビット）
openssl genrsa -out private.key 4096

# 公開鍵の生成
openssl rsa -in private.key -pubout -out public.key
```

生成した公開鍵（`public.key`の内容）をCDataサポートチームに登録します。秘密鍵（`private.key`）は `.env` の `CONNECT_AI_PRIVATE_KEY` に設定します。

---

## 5. 依存ライブラリ

### 5.1 backend/requirements.txt

```text
# Webフレームワーク
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-Migrate==4.0.5

# データバリデーション
pydantic==2.5.0

# 認証・暗号化
bcrypt==4.1.2
PyJWT==2.8.0
cryptography==41.0.7

# HTTPクライアント
requests==2.31.0

# 環境変数
python-dotenv==1.0.0

# DB
# SQLite は Python 標準ライブラリのため追加不要
```

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
| タイムアウト | SQL APIのタイムアウト最大300秒 |
| コネクション作成 | `redirectURL`は必須。ローカル開発では`http://localhost:5000/callback`を使用 |

### 6.2 ローカル開発の制約

| 制約 | 内容 |
|------|------|
| HTTPSなし | ローカル開発ではHTTP。本番移行時はHTTPS対応が必要 |
| シングルプロセス | FlaskのDev ServerはシングルスレッドのためConcurrentリクエストに非対応 |
| SQLite | マルチプロセス書き込みに非対応。デモ用途のみ使用 |

### 6.3 セキュリティに関する注意事項

- `SECRET_KEY` と `CONNECT_AI_PRIVATE_KEY` はGitにコミットしないこと（`.gitignore`に`.env`を追加）
- デモ環境であっても、RSA秘密鍵は厳重に管理すること
- ユーザー入力をSQL文に直接埋め込まず、必ずConnect AI APIの`parameters`オプションを使用すること

### 6.4 データソースの`name`について

Connect AI Connection APIの`name`パラメータに指定した値が、その後のMetadata/SQL APIで`catalogName`として使用されます。コネクション名は英数字とハイフン・アンダースコアのみ使用することを推奨します（スペースや特殊文字を避ける）。

---

**承認者**: _________________
**承認日**: _________________
