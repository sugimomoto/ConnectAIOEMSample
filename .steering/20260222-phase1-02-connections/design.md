# 設計: Phase 1-02 コネクション管理

**作業ディレクトリ**: `.steering/20260222-phase1-02-connections/`
**作成日**: 2026-02-23

---

## 目次

1. [実装アプローチ](#1-実装アプローチ)
2. [ディレクトリ構成](#2-ディレクトリ構成)
3. [バックエンド設計](#3-バックエンド設計)
4. [フロントエンド設計](#4-フロントエンド設計)
5. [環境変数](#5-環境変数)
6. [テスト設計](#6-テスト設計)

---

## 1. 実装アプローチ

### ローカル DB 非保存

コネクション情報はローカル DB に保存しない。
すべての操作（一覧・作成・削除）は Connect AI API を直接呼び出す。

| 操作 | Connect AI API |
|------|---------------|
| データソース一覧 | `GET /poweredby/datasources` |
| コネクション作成 | `POST /poweredby/connection/create` |
| コネクション一覧 | `GET /poweredby/connections` |
| コネクション削除 | `DELETE /poweredby/connection/delete` |

### テナント分離

JWT の `sub` クレームに `ChildAccountId` をセットすることで、Connect AI 側が自動的にそのユーザーのデータのみを返す。
ローカルでの `user_id` フィルタは不要。

### コールバックフロー

Connect AI での認証完了後は `/callback` へリダイレクトされる。
バックエンドへの activate API 呼び出しは不要で、フロントエンドが直接 `/connections` へリダイレクトする。

---

## 2. ディレクトリ構成

本作業で追加・変更するファイル：

```
ConnectAIOEMSample/
├── backend/
│   ├── connectai/
│   │   └── client.py          # get_datasources() / get_connections()
│   │                          # create_connection() / delete_connection() を追加
│   ├── schemas/
│   │   └── connection_schema.py   # CreateConnectionSchema
│   ├── services/
│   │   └── connection_service.py  # コネクション操作ロジック
│   ├── api/
│   │   └── v1/
│   │       ├── __init__.py    # connections Blueprint を追加
│   │       └── connections.py # コネクション API エンドポイント
│   └── tests/
│       └── test_connections.py
├── frontend/
│   ├── pages/
│   │   ├── connections.html       # コネクション一覧画面
│   │   ├── connections-new.html   # コネクション作成フォーム画面
│   │   └── callback.html          # コールバック受け取り画面
│   └── static/js/
│       └── api-client.js          # コネクション関連メソッドを追加
└── backend/
    └── .env.example               # APP_BASE_URL を追加
```

---

## 3. バックエンド設計

### 3.1 connectai/client.py（追加メソッド）

既存の `ConnectAIClient` クラスに以下のメソッドを追加する。

```python
def _get(self, path: str) -> dict:
    url = f"{self.base_url}{path}"
    try:
        resp = requests.get(url, headers=self._headers(), timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.HTTPError as e:
        raise ConnectAIError(f"HTTP {e.response.status_code}: {e.response.text}") from e
    except requests.RequestException as e:
        raise ConnectAIError(f"Request failed: {e}") from e

def _delete(self, path: str, payload: dict) -> dict:
    url = f"{self.base_url}{path}"
    try:
        resp = requests.delete(url, json=payload, headers=self._headers(), timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.HTTPError as e:
        raise ConnectAIError(f"HTTP {e.response.status_code}: {e.response.text}") from e
    except requests.RequestException as e:
        raise ConnectAIError(f"Request failed: {e}") from e

def get_datasources(self) -> list[dict]:
    """
    利用可能なデータソース一覧を返す。

    Returns:
        [{"name": "Salesforce", ...}, ...]
    """
    data = self._get("/poweredby/datasources")
    return data.get("datasources", data) if isinstance(data, dict) else data

def get_connections(self) -> list[dict]:
    """
    ChildAccountId に紐づくコネクション一覧を返す。

    Returns:
        [{"id": "...", "name": "...", "dataSource": "...", "status": "..."}, ...]
    """
    data = self._get("/poweredby/connections")
    return data.get("connections", data) if isinstance(data, dict) else data

def create_connection(self, name: str, data_source: str, redirect_url: str) -> str:
    """
    コネクションを作成し、Connect AI の認証画面 URL を返す。

    Args:
        name: コネクション名
        data_source: データソース種別（例: "Salesforce"）
        redirect_url: 認証完了後のリダイレクト先 URL
    Returns:
        Connect AI の認証画面 URL
    """
    data = self._post("/poweredby/connection/create", {
        "name": name,
        "dataSource": data_source,
        "redirectURL": redirect_url,
    })
    return data["redirectURL"]

def delete_connection(self, connection_id: str) -> None:
    """
    コネクションを削除する。

    Args:
        connection_id: Connect AI 側のコネクション ID
    """
    self._delete("/poweredby/connection/delete", {"connectionId": connection_id})
```

### 3.2 schemas/connection_schema.py

```python
from pydantic import BaseModel


class CreateConnectionSchema(BaseModel):
    name: str
    data_source: str
```

### 3.3 services/connection_service.py

```python
from flask import current_app
from flask_login import current_user
from backend.connectai.client import ConnectAIClient
from backend.connectai.exceptions import ConnectAIError


class ConnectionService:

    def _client(self) -> ConnectAIClient:
        """ログイン中ユーザーの ChildAccountId で Connect AI クライアントを生成する。"""
        return ConnectAIClient(child_account_id=current_user.connect_ai_account_id)

    def get_datasources(self) -> list[dict]:
        """データソース一覧を Connect AI から取得する。"""
        return self._client().get_datasources()

    def get_connections(self) -> list[dict]:
        """コネクション一覧を Connect AI から取得する。"""
        return self._client().get_connections()

    def create_connection(self, name: str, data_source: str) -> str:
        """
        コネクションを作成し、Connect AI の認証画面 URL を返す。

        Raises:
            ValueError: connect_ai_account_id が未設定の場合
            ConnectAIError: Connect AI API 呼び出し失敗
        """
        if not current_user.connect_ai_account_id:
            raise ValueError("Connect AI アカウントが未設定です。管理者にお問い合わせください。")

        redirect_url = f"{current_app.config['APP_BASE_URL']}/callback"
        return self._client().create_connection(name, data_source, redirect_url)

    def delete_connection(self, connection_id: str) -> None:
        """
        Connect AI 側のコネクションを削除する。

        Raises:
            ConnectAIError: Connect AI API 呼び出し失敗
        """
        self._client().delete_connection(connection_id)
```

### 3.4 api/v1/connections.py

```python
from flask import jsonify, request
from flask_login import login_required
from backend.api.v1 import api_v1_bp
from backend.services.connection_service import ConnectionService
from backend.schemas.connection_schema import CreateConnectionSchema
from backend.connectai.exceptions import ConnectAIError
from pydantic import ValidationError

connection_service = ConnectionService()


@api_v1_bp.route("/api/v1/datasources", methods=["GET"])
@login_required
def get_datasources():
    try:
        datasources = connection_service.get_datasources()
    except ConnectAIError as e:
        return jsonify({"error": {"code": "CONNECT_AI_ERROR", "message": str(e)}}), 502
    return jsonify({"datasources": datasources}), 200


@api_v1_bp.route("/api/v1/connections", methods=["GET"])
@login_required
def get_connections():
    try:
        connections = connection_service.get_connections()
    except ConnectAIError as e:
        return jsonify({"error": {"code": "CONNECT_AI_ERROR", "message": str(e)}}), 502
    return jsonify({"connections": connections}), 200


@api_v1_bp.route("/api/v1/connections", methods=["POST"])
@login_required
def create_connection():
    try:
        schema = CreateConnectionSchema(**request.get_json())
    except ValidationError as e:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": e.errors()}}), 400

    try:
        redirect_url = connection_service.create_connection(schema.name, schema.data_source)
    except ValueError as e:
        return jsonify({"error": {"code": "FORBIDDEN", "message": str(e)}}), 403
    except ConnectAIError as e:
        return jsonify({"error": {"code": "CONNECT_AI_ERROR", "message": str(e)}}), 502

    return jsonify({"redirectURL": redirect_url}), 201


@api_v1_bp.route("/api/v1/connections/<connection_id>", methods=["DELETE"])
@login_required
def delete_connection(connection_id: str):
    try:
        connection_service.delete_connection(connection_id)
    except ConnectAIError as e:
        return jsonify({"error": {"code": "CONNECT_AI_ERROR", "message": str(e)}}), 502
    return jsonify({"message": "削除しました"}), 200
```

### 3.5 api/v1/__init__.py（変更）

```python
from flask import Blueprint

api_v1_bp = Blueprint("api_v1", __name__)

from . import auth        # noqa: E402, F401
from . import connections # noqa: E402, F401
```

---

## 4. フロントエンド設計

### 4.1 api-client.js（追加メソッド）

```javascript
async getDatasources() {
  return this.request('GET', '/datasources');
}

async getConnections() {
  return this.request('GET', '/connections');
}

async createConnection(name, dataSource) {
  return this.request('POST', '/connections', { name, data_source: dataSource });
}

async deleteConnection(connectionId) {
  return this.request('DELETE', `/connections/${connectionId}`);
}
```

### 4.2 connections.html（コネクション一覧画面）

- Alpine.js でコネクション一覧を管理
- ページ読み込み時に `GET /api/v1/connections` を呼び出して一覧を表示
- 各コネクションに削除ボタンを配置（確認ダイアログ付き）
- 「新規作成」ボタンで `/connections/new` へ遷移

### 4.3 connections-new.html（コネクション作成フォーム）

- ページ読み込み時に `GET /api/v1/datasources` を呼び出しセレクトボックスを構築
- コネクション名（テキスト入力）とデータソース（セレクトボックス）を入力
- 「作成」ボタン押下で `POST /api/v1/connections` → `redirectURL` を取得後、Connect AI 画面へリダイレクト

### 4.4 callback.html（コールバック受け取り画面）

- 「接続が完了しました」のメッセージを表示
- 3秒後（または即座に）`/connections` へ自動リダイレクト
- バックエンドへの API 呼び出しは不要

---

## 5. 環境変数

### backend/.env.example（追加）

```bash
# アプリのベース URL（コールバック URL の組み立てに使用）
APP_BASE_URL=http://localhost:5001
```

### backend/config.py（追加）

```python
APP_BASE_URL: str = os.environ.get("APP_BASE_URL", "http://localhost:5001")
```

---

## 6. テスト設計

### 6.1 テストファーストの進め方

Phase 1-01 と同様に TDD で進める。

```
[フェーズ1] 基盤スタブ作成（schemas / service の空実装）
     ↓
[フェーズ2] テスト実装（conftest 追加・test_connections.py）
     ↓
[レビュー] テストコードのレビュー依頼
     ↓
[フェーズ3] バックエンド実装（テストを PASS させる）
```

### 6.2 conftest.py への追加

```python
@pytest.fixture
def mock_connect_ai_connections():
    """Connect AI コネクション関連 API をモックする"""
    with patch("backend.connectai.client.ConnectAIClient.get_datasources") as mock_ds, \
         patch("backend.connectai.client.ConnectAIClient.get_connections") as mock_list, \
         patch("backend.connectai.client.ConnectAIClient.create_connection") as mock_create, \
         patch("backend.connectai.client.ConnectAIClient.delete_connection") as mock_delete:

        mock_ds.return_value = [{"name": "Salesforce"}, {"name": "QuickBooks"}]
        mock_list.return_value = [
            {"id": "conn-001", "name": "My SF", "dataSource": "Salesforce", "status": "active"}
        ]
        mock_create.return_value = "https://cloud.cdata.com/connect/auth/..."
        mock_delete.return_value = None
        yield {
            "datasources": mock_ds,
            "list": mock_list,
            "create": mock_create,
            "delete": mock_delete,
        }
```

### 6.3 テストケース一覧

| # | テスト関数名 | 検証内容 | 期待レスポンス |
|---|------------|---------|-------------|
| 1 | `test_get_datasources_success` | データソース一覧取得 | 200 + datasources 配列 |
| 2 | `test_get_datasources_requires_login` | 未認証でのデータソース取得 | 401 |
| 3 | `test_get_connections_success` | コネクション一覧取得 | 200 + connections 配列 |
| 4 | `test_get_connections_requires_login` | 未認証でのコネクション一覧 | 401 |
| 5 | `test_create_connection_success` | 正常なコネクション作成 | 201 + redirectURL |
| 6 | `test_create_connection_without_child_account` | ChildAccountId 未設定ユーザーの作成 | 403 |
| 7 | `test_create_connection_requires_login` | 未認証でのコネクション作成 | 401 |
| 8 | `test_delete_connection_success` | 正常なコネクション削除 | 200 |
| 9 | `test_delete_connection_requires_login` | 未認証でのコネクション削除 | 401 |

### 6.4 モック方針

| モック対象 | 方針 |
|-----------|------|
| `ConnectAIClient.get_datasources` | fixture でモック（テスト用データを返す） |
| `ConnectAIClient.get_connections` | fixture でモック |
| `ConnectAIClient.create_connection` | fixture でモック（redirectURL を返す） |
| `ConnectAIClient.delete_connection` | fixture でモック（None を返す） |
