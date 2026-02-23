# 設計: Phase 1-01 認証・アカウント管理

**作業ディレクトリ**: `.steering/20260222-phase1-01-auth/`
**作成日**: 2026-02-22

---

## 目次

1. [実装アプローチ](#1-実装アプローチ)
2. [ディレクトリ構成](#2-ディレクトリ構成)
3. [データモデル](#3-データモデル)
4. [バックエンド設計](#4-バックエンド設計)
5. [フロントエンド設計](#5-フロントエンド設計)
6. [環境変数](#6-環境変数)
7. [依存ライブラリ](#7-依存ライブラリ)
8. [テスト設計](#8-テスト設計)

---

## 1. 実装アプローチ

### セッション管理

- **Flask-Login** を使用したCookieベースのセッション管理
- フロントエンドでのトークン管理（localStorage）は行わない
- ブラウザがCookieを自動付与するため、APIリクエスト時の認証ヘッダー操作は不要

### Connect AI JWT

- Connect AI APIを呼び出す**都度**、バックエンドで RS256 JWT を生成する
- RSA秘密鍵は `backend/keys/private.key` から読み込む
- フロントエンドには渡さない

### Connect AI Account API の呼び出しタイミング

ユーザー登録時に1度だけ呼び出す。この時点では子アカウントが存在しないため、
JWTの `sub` には `ParentAccountId` をセットして親アカウント自身として呼び出す。

```
JWT payload (Account API呼び出し時):
{
  "tokenType": "powered-by",
  "iss": ParentAccountId,
  "sub": "",   ← 子アカウント未作成のため空文字列
  "iat": <now>,
  "exp": <now + 3600>
}
```

以降のAPIコール（コネクション作成等）では `sub` に `ChildAccountId` をセットする。

---

## 2. ディレクトリ構成

本作業で作成するファイルの配置：

```
ConnectAIOEMSample/
├── backend/
│   ├── app.py                        # Flaskアプリ初期化・Blueprint登録・Flask-Login設定
│   ├── config.py                     # 環境変数読み込み・設定クラス
│   ├── keys/
│   │   ├── private.key               # RSA秘密鍵（gitignore済み）
│   │   ├── public.key                # RSA公開鍵（gitignore済み）
│   │   └── README.md
│   ├── models/
│   │   ├── __init__.py               # db = SQLAlchemy() の生成
│   │   └── user.py                   # User モデル（Flask-Login の UserMixin 継承）
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── user_schema.py            # RegisterSchema / LoginSchema
│   ├── services/
│   │   ├── __init__.py
│   │   └── auth_service.py           # 登録・認証・Connect AI Account API呼び出し
│   ├── connectai/
│   │   ├── __init__.py
│   │   ├── jwt.py                    # RS256 JWT 生成
│   │   ├── client.py                 # Connect AI HTTP クライアント
│   │   └── exceptions.py             # ConnectAIError
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py           # Blueprint 定義・登録
│   │       └── auth.py               # /api/v1/auth/* エンドポイント
│   ├── middleware/
│   │   ├── __init__.py
│   │   └── error_handler.py          # グローバルエラーハンドラー
│   ├── migrations/                   # Alembic マイグレーション
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   └── test_auth.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── pages/
│   │   ├── login.html
│   │   ├── register.html
│   │   └── dashboard.html
│   └── static/
│       └── js/
│           ├── api-client.js
│           └── auth.js
├── .env.example
└── .gitignore
```

---

## 3. データモデル

### users テーブル

```python
# backend/models/user.py
from flask_login import UserMixin
from . import db

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id                    = db.Column(db.Integer, primary_key=True)
    email                 = db.Column(db.String(255), unique=True, nullable=False)
    password_hash         = db.Column(db.String(255), nullable=False)
    name                  = db.Column(db.String(100), nullable=False)
    connect_ai_account_id = db.Column(db.String(255), nullable=True)  # ChildAccountId
    created_at            = db.Column(db.DateTime, server_default=db.func.now())
    updated_at            = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
```

- `connect_ai_account_id` は登録直後は `NULL`、Account API 呼び出し成功後に `ChildAccountId` で更新される
- `UserMixin` を継承することで Flask-Login が要求する `is_authenticated`, `get_id()` 等が自動実装される

---

## 4. バックエンド設計

### 4.1 app.py

```python
from flask import Flask
from flask_login import LoginManager
from backend.models import db
from backend.api.v1 import api_v1_bp
from backend.middleware.error_handler import register_error_handlers

def create_app():
    app = Flask(
        __name__,
        static_folder="../frontend/static",
        template_folder="../frontend/pages",
    )
    app.config.from_object("backend.config.Config")

    db.init_app(app)

    login_manager = LoginManager(app)
    login_manager.login_view = "auth.login_page"   # 未認証時のリダイレクト先

    @login_manager.user_loader
    def load_user(user_id):
        from backend.models.user import User
        return db.session.get(User, int(user_id))

    # APIの未認証アクセスは401を返す（HTMLリダイレクトではなく）
    @login_manager.unauthorized_handler
    def unauthorized():
        from flask import request, jsonify, redirect, url_for
        if request.path.startswith("/api/"):
            return jsonify({"error": {"code": "UNAUTHORIZED"}}), 401
        return redirect(url_for("auth.login_page"))

    app.register_blueprint(api_v1_bp, url_prefix="/api/v1")
    register_error_handlers(app)

    return app
```

### 4.2 connectai/jwt.py

```python
import time
import jwt
from cryptography.hazmat.primitives import serialization

def generate_connect_ai_jwt(parent_account_id: str, subject_account_id: str) -> str:
    """
    Connect AI API 用 RS256 JWT を生成する。

    Args:
        parent_account_id: ParentAccountId（iss クレーム）
        subject_account_id: 呼び出し対象アカウントID（sub クレーム）
                            子アカウント未作成時は ParentAccountId と同値にする

    Returns:
        署名済み JWT 文字列
    """
    private_key_path = "backend/keys/private.key"
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

### 4.3 connectai/client.py

```python
import os
import requests
from .jwt import generate_connect_ai_jwt
from .exceptions import ConnectAIError

class ConnectAIClient:
    """
    Connect AI HTTP API クライアント。
    各メソッド呼び出し時に JWT を生成してリクエストに付与する。
    """

    def __init__(self, child_account_id: str):
        self.base_url = os.environ["CONNECT_AI_BASE_URL"]
        self.parent_account_id = os.environ["CONNECT_AI_PARENT_ACCOUNT_ID"]
        # 子アカウント未作成の場合は空文字列を使う
        self.subject_id = child_account_id if child_account_id is not None else ""

    def _headers(self) -> dict:
        token = generate_connect_ai_jwt(self.parent_account_id, self.subject_id)
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    def _post(self, path: str, payload: dict) -> dict:
        url = f"{self.base_url}{path}"
        try:
            resp = requests.post(url, json=payload, headers=self._headers(), timeout=30)
            resp.raise_for_status()
            return resp.json()
        except requests.HTTPError as e:
            raise ConnectAIError(f"HTTP {e.response.status_code}: {e.response.text}") from e
        except requests.RequestException as e:
            raise ConnectAIError(f"Request failed: {e}") from e

    def create_account(self, external_id: str) -> str:
        """
        子アカウントを作成し、ChildAccountId を返す。

        Args:
            external_id: アプリ側のユーザーID（文字列）
        Returns:
            ChildAccountId（Connect AI が発行する accountId）
        """
        data = self._post("/poweredby/account/create", {"externalId": external_id})
        return data["accountId"]  # Connect AI 側のフィールド名は accountId
```

### 4.4 services/auth_service.py

```python
import bcrypt
from flask_login import login_user, logout_user
from backend.models import db
from backend.models.user import User
from backend.connectai.client import ConnectAIClient
from backend.connectai.exceptions import ConnectAIError

class AuthService:

    def register(self, email: str, password: str, name: str) -> tuple[User, str | None]:
        """
        ユーザー登録。Connect AI 子アカウントの作成も行う。

        Returns:
            (User, error_message)
            Connect AI API 失敗時は User を返しつつ error_message に詳細を返す
        """
        # 重複チェック
        if User.query.filter_by(email=email).first():
            raise ValueError("このメールアドレスはすでに登録されています")

        # パスワードハッシュ化
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=10)).decode()

        # ユーザー作成
        user = User(email=email, password_hash=password_hash, name=name)
        db.session.add(user)
        db.session.commit()

        # Connect AI 子アカウント作成
        error_msg = None
        try:
            client = ConnectAIClient(child_account_id=None)  # 子未作成のため None
            child_account_id = client.create_account(str(user.id))
            user.connect_ai_account_id = child_account_id
            db.session.commit()
        except ConnectAIError as e:
            # API失敗でもユーザーは作成済みのため、エラーメッセージのみ返す
            error_msg = f"アカウント作成は完了しましたが、Connect AI連携に失敗しました: {e}"

        login_user(user)
        return user, error_msg

    def login(self, email: str, password: str) -> User:
        """
        メール・パスワードを検証してセッションを開始する。

        Raises:
            ValueError: 認証失敗
        """
        user = User.query.filter_by(email=email).first()
        if not user:
            raise ValueError("メールアドレスまたはパスワードが正しくありません")

        if not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
            raise ValueError("メールアドレスまたはパスワードが正しくありません")

        login_user(user)
        return user

    def logout(self):
        logout_user()
```

### 4.5 api/v1/auth.py

```python
from flask import Blueprint, request, jsonify, redirect, url_for, render_template
from flask_login import login_required, current_user
from backend.services.auth_service import AuthService
from backend.schemas.user_schema import RegisterSchema, LoginSchema

auth_bp = Blueprint("auth", __name__)
auth_service = AuthService()

# --- ページルーティング ---

@auth_bp.route("/login")
def login_page():
    return render_template("login.html")

@auth_bp.route("/register")
def register_page():
    return render_template("register.html")

@auth_bp.route("/dashboard")
@login_required
def dashboard_page():
    return render_template("dashboard.html")

# --- API ---

@auth_bp.route("/api/v1/auth/register", methods=["POST"])
def register():
    try:
        schema = RegisterSchema(**request.get_json())
    except Exception as e:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": str(e)}}), 400

    try:
        user, warning = auth_service.register(schema.email, schema.password, schema.name)
    except ValueError as e:
        return jsonify({"error": {"code": "CONFLICT", "message": str(e)}}), 409

    resp = {"user": {"id": user.id, "email": user.email, "name": user.name}}
    if warning:
        resp["warning"] = warning
    return jsonify(resp), 201

@auth_bp.route("/api/v1/auth/login", methods=["POST"])
def login():
    try:
        schema = LoginSchema(**request.get_json())
    except Exception as e:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": str(e)}}), 400

    try:
        user = auth_service.login(schema.email, schema.password)
    except ValueError as e:
        return jsonify({"error": {"code": "UNAUTHORIZED", "message": str(e)}}), 401

    return jsonify({"user": {"id": user.id, "email": user.email, "name": user.name}}), 200

@auth_bp.route("/api/v1/auth/logout", methods=["POST"])
@login_required
def logout():
    auth_service.logout()
    return jsonify({"message": "ログアウトしました"}), 200

@auth_bp.route("/api/v1/auth/me", methods=["GET"])
@login_required
def me():
    return jsonify({
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "name": current_user.name,
            "connect_ai_account_id": current_user.connect_ai_account_id,
        }
    }), 200
```

---

## 5. フロントエンド設計

### 5.1 api-client.js

CookieはブラウザがAutoで付与するため、認証ヘッダーの操作は不要。
`credentials: "include"` を指定して Cookie を送信する。

```javascript
class APIClient {
    constructor(baseURL = '/api/v1') {
        this.baseURL = baseURL;
    }

    async request(method, endpoint, data = null) {
        const options = {
            method,
            credentials: 'include',       // Cookie を自動送信
            headers: { 'Content-Type': 'application/json' },
        };
        if (data) options.body = JSON.stringify(data);

        const resp = await fetch(`${this.baseURL}${endpoint}`, options);

        if (resp.status === 401) {
            window.location.href = '/login';
            return;
        }
        if (!resp.ok) {
            const err = await resp.json();
            throw new Error(err.error?.message || 'エラーが発生しました');
        }
        return resp.json();
    }

    async register(email, password, name) {
        return this.request('POST', '/auth/register', { email, password, name });
    }

    async login(email, password) {
        return this.request('POST', '/auth/login', { email, password });
    }

    async logout() {
        return this.request('POST', '/auth/logout');
    }

    async getMe() {
        return this.request('GET', '/auth/me');
    }
}
```

### 5.2 login.html / register.html の構成

- Alpine.js で送信状態・エラーメッセージを管理
- フォーム送信 → `APIClient` 経由でAPIコール → 成功時 `/dashboard` へリダイレクト

---

## 6. 環境変数

### backend/.env.example

```bash
# Flask
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=change-me-to-a-random-string   # Flaskセッション署名用

# データベース
DATABASE_URL=sqlite:///datahub.db

# CData Connect AI
CONNECT_AI_BASE_URL=https://cloud.cdata.com/api
CONNECT_AI_PARENT_ACCOUNT_ID=your-parent-account-id

# RSA秘密鍵ファイルパス（backend/keys/private.key を使用）
CONNECT_AI_PRIVATE_KEY_PATH=backend/keys/private.key
```

> `CONNECT_AI_PRIVATE_KEY_PATH` でファイルパスを指定し、`connectai/jwt.py` がファイルから読み込む方式を採用する。
> これにより `.env` に長い秘密鍵文字列を直書きせずに済む。

---

## 7. 依存ライブラリ

### backend/requirements.txt（本作業で確定する部分）

```text
# Webフレームワーク
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-Migrate==4.0.5
Flask-Login==0.6.3

# データバリデーション
pydantic==2.5.0

# 認証・暗号化
bcrypt==4.1.2
PyJWT==2.8.0
cryptography==41.0.7

# HTTPクライアント（Connect AI API呼び出し用）
requests==2.31.0

# 環境変数
python-dotenv==1.0.0
```

**注**: PyJWT と cryptography は Connect AI JWT（RS256）の生成のみに使用する。
アプリのセッション管理は Flask-Login + Flask 標準セッションで行うため JWT は不要。

---

## 8. テスト設計

### 8.1 テストファーストの進め方

本作業はテストファースト（TDD）で進める。

```
[フェーズ1] 基盤スタブ作成
  └─ モデル・スキーマ・例外クラスなど import できる最低限の構造を用意
       ↓
[フェーズ2] テスト実装
  └─ conftest.py と test_auth.py を実装
  └─ この時点ではテストは全て FAIL する（実装がないため）
       ↓
[レビュー] テストコードのレビュー依頼
  └─ ケースの網羅性・モック方針を確認後、次フェーズへ
       ↓
[フェーズ3] バックエンド実装
  └─ テストが PASS するよう実装を進める
```

### 8.2 テスト環境の構成

```python
# backend/tests/conftest.py

import pytest
from unittest.mock import patch
from backend.app import create_app
from backend.models import db as _db

@pytest.fixture
def app():
    """テスト用Flaskアプリ（in-memory SQLite）"""
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "test-secret",
        "WTF_CSRF_ENABLED": False,
    })
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture(autouse=True)
def mock_connect_ai():
    """Connect AI Account API をモックする（外部APIへの依存を排除）"""
    with patch("backend.connectai.client.ConnectAIClient.create_account") as mock:
        mock.return_value = "mock-child-account-id-001"
        yield mock
```

### 8.3 テストケース一覧

| # | テスト関数名 | 検証内容 | 期待レスポンス |
|---|------------|---------|-------------|
| 1 | `test_register_success` | 正常なユーザー登録 | 201 + user オブジェクト |
| 2 | `test_register_duplicate_email` | 重複メールアドレスでの登録 | 409 |
| 3 | `test_register_saves_child_account_id` | 登録後に `connect_ai_account_id` が保存される | DB確認 |
| 4 | `test_register_password_is_hashed` | パスワードがbcryptハッシュで保存される | DB確認（平文でないこと） |
| 5 | `test_login_success` | 正常なログイン | 200 + Cookie発行 |
| 6 | `test_login_wrong_password` | パスワード不一致でのログイン | 401 |
| 7 | `test_login_unknown_email` | 未登録メールでのログイン | 401 |
| 8 | `test_protected_api_without_login` | 未認証での `/api/v1/auth/me` アクセス | 401 |
| 9 | `test_logout_destroys_session` | ログアウト後に保護APIへアクセス | 401 |

### 8.4 モック方針

| モック対象 | 方針 | 理由 |
|-----------|------|------|
| `ConnectAIClient.create_account` | `unittest.mock.patch` でモック | 外部API（Connect AI）への依存を排除し、テストを高速・安定させる |
| `connectai/jwt.py` | モック不要 | RSA鍵の代わりにテスト用の鍵を生成して使用するか、jwt.pyごとモックする |
| DB（SQLite） | in-memory SQLite を使用 | 実際のDBファイルを汚染せず、テストごとにクリーンな状態を保つ |
