# 設計書: Phase 3-01 Connect AI API リクエストログ

**作業ディレクトリ**: `.steering/20260223-phase3-01-api-log/`
**作成日**: 2026-02-23
**GitHub Issue**: #1

---

## 1. 実装アプローチ

### 1.1 全体方針

`ConnectAIClient` の低レベルメソッド（`_get()` / `_post()` / `_delete()`）にログ記録処理を横断的に追加する。
サービス層・ルート層には変更を加えず、クライアント層のみで完結させる。

ログの DB 書き込みは `threading.Thread` でバックグラウンド実行し、メイン処理をブロックしない。

### 1.2 `current_user` とスレッドの扱い

Flask-Login の `current_user` はリクエストコンテキストに紐付くプロキシのため、スレッド内では参照できない。

**対応策**: メインスレッドで `current_user.id` を取得してからスレッドに渡す。

```
メインスレッド（リクエストコンテキストあり）
  └─ current_user.id を取得
  └─ threading.Thread(target=_save, args=(app, user_id, log_data)).start()
       └─ サブスレッド（with app.app_context()）
            └─ ApiLog(..., user_id=user_id)
            └─ db.session.commit()
```

ユーザー未認証（`current_user.is_authenticated == False`）の場合はログをスキップする。
（例: 登録フローの `create_account()` 呼び出し時）

---

## 2. データモデル

### 2.1 `ApiLog` モデル（新規）

**ファイル**: `backend/models/api_log.py`

```python
from . import db

class ApiLog(db.Model):
    __tablename__ = "api_logs"

    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    timestamp    = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    method       = db.Column(db.String(10),  nullable=False)   # "GET" / "POST" / "DELETE"
    endpoint     = db.Column(db.String(255), nullable=False)   # "/query", "/catalogs", ...
    request_body = db.Column(db.Text, nullable=True)           # JSON 文字列（GET は NULL）
    response_body= db.Column(db.Text, nullable=True)           # JSON 文字列
    status_code  = db.Column(db.Integer, nullable=False)
    elapsed_ms   = db.Column(db.Integer, nullable=False)

    user = db.relationship("User", backref=db.backref("api_logs", lazy=True))
```

### 2.2 `models/__init__.py` への追加

```python
from .api_log import ApiLog  # noqa: F401
```

### 2.3 DB マイグレーション

実装後に以下を実行：

```bash
flask db migrate -m "add api_logs table"
flask db upgrade
```

---

## 3. `ConnectAIClient` の変更

**ファイル**: `backend/connectai/client.py`

### 3.1 ログ書き込みヘルパー追加

クラスの外側に `_save_log_async()` を定義する（循環インポートを避けるため）。

```python
import json
import threading
import time
from flask import current_app
from flask_login import current_user


def _save_log_async(app, user_id: int, method: str, endpoint: str,
                    request_body: str | None, response_body: str | None,
                    status_code: int, elapsed_ms: int) -> None:
    def _save():
        with app.app_context():
            try:
                from backend.models.api_log import ApiLog
                from backend.models import db
                log = ApiLog(
                    user_id=user_id,
                    method=method,
                    endpoint=endpoint,
                    request_body=request_body,
                    response_body=response_body,
                    status_code=status_code,
                    elapsed_ms=elapsed_ms,
                )
                db.session.add(log)
                db.session.commit()
            except Exception:
                pass  # サイレントに無視
    threading.Thread(target=_save, daemon=True).start()
```

### 3.2 `_get()` の変更（抜粋）

```python
def _get(self, path: str, params: dict | None = None) -> dict:
    url = f"{self.base_url}{path}"
    start = time.monotonic()
    try:
        resp = requests.get(url, headers=self._headers(), params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        self._log(path, "GET", None, data, resp.status_code, start)
        return data
    except requests.HTTPError as e:
        self._log(path, "GET", None, {"error": e.response.text}, e.response.status_code, start)
        raise ConnectAIError(...)
    ...
```

### 3.3 `_log()` インスタンスメソッド追加

```python
def _log(self, path: str, method: str, request_body,
         response_body, status_code: int, start: float) -> None:
    if not current_user.is_authenticated:
        return
    try:
        user_id = current_user.id
        app = current_app._get_current_object()
        elapsed_ms = int((time.monotonic() - start) * 1000)
        _save_log_async(
            app=app,
            user_id=user_id,
            method=method,
            endpoint=path,
            request_body=json.dumps(request_body, ensure_ascii=False) if request_body else None,
            response_body=json.dumps(response_body, ensure_ascii=False) if response_body else None,
            status_code=status_code,
            elapsed_ms=elapsed_ms,
        )
    except Exception:
        pass  # ログ処理でのエラーは本体に伝播させない
```

---

## 4. サービス層

**ファイル**: `backend/services/api_log_service.py`（新規）

```python
from backend.models.api_log import ApiLog
from backend.models import db


class ApiLogService:
    def list_logs(self, user_id: int, limit: int = 50, offset: int = 0) -> dict:
        query = ApiLog.query.filter_by(user_id=user_id).order_by(ApiLog.timestamp.desc())
        total = query.count()
        logs = query.limit(limit).offset(offset).all()
        return {
            "logs": [self._to_dict(log) for log in logs],
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    def clear_logs(self, user_id: int) -> None:
        ApiLog.query.filter_by(user_id=user_id).delete()
        db.session.commit()

    def _to_dict(self, log: ApiLog) -> dict:
        return {
            "id": log.id,
            "timestamp": log.timestamp.isoformat(),
            "method": log.method,
            "endpoint": log.endpoint,
            "status_code": log.status_code,
            "elapsed_ms": log.elapsed_ms,
            "request_body": log.request_body,
            "response_body": log.response_body,
        }
```

---

## 5. ルート層

**ファイル**: `backend/api/v1/api_log.py`（新規）

| メソッド | パス                | 説明 |
|---------|-------------------|------|
| GET     | `/api-log`        | 一覧画面（HTML） |
| GET     | `/api/v1/api-logs` | 一覧取得（JSON） |
| DELETE  | `/api/v1/api-logs` | 自ユーザーのログ全件削除 |

```python
from flask import jsonify, request, render_template
from flask_login import login_required, current_user
from pydantic import ValidationError
from backend.api.v1 import api_v1_bp
from backend.services.api_log_service import ApiLogService

api_log_service = ApiLogService()


@api_v1_bp.route("/api-log")
@login_required
def api_log_page():
    return render_template("api-log.html")


@api_v1_bp.route("/api/v1/api-logs", methods=["GET"])
@login_required
def get_api_logs():
    limit = min(int(request.args.get("limit", 50)), 200)
    offset = int(request.args.get("offset", 0))
    result = api_log_service.list_logs(current_user.id, limit, offset)
    return jsonify(result), 200


@api_v1_bp.route("/api/v1/api-logs", methods=["DELETE"])
@login_required
def clear_api_logs():
    api_log_service.clear_logs(current_user.id)
    return jsonify({"message": "ログをクリアしました"}), 200
```

---

## 6. フロントエンド

### 6.1 `api-client.js` に追加

```javascript
async getApiLogs(limit = 50, offset = 0) {
    return this._fetch(`/api/v1/api-logs?limit=${limit}&offset=${offset}`);
}

async clearApiLogs() {
    return this._fetch('/api/v1/api-logs', { method: 'DELETE' });
}
```

### 6.2 `api-log.html` の画面構成

```
┌─────────────────────────────────────────────────────────┐
│  API ログ                          [ログをクリア]         │
├────────────────────────────────────────────────────────── ┤
│  タイムスタンプ       メソッド  エンドポイント  ステータス  時間 │
│  2026-02-23 10:01   POST     /query          200       342ms│
│  2026-02-23 10:00   GET      /catalogs       200        87ms│
│  ...                                                     │
├─────────────────────────────────────────────────────────┤
│  [← 前へ]  1〜50件目 / 全 120件  [次へ →]               │
└─────────────────────────────────────────────────────────┘

[行クリック時のモーダル]
┌─────────────────────────────────────────────────────────┐
│  POST /query — 200  (342ms)                       [×]   │
├────────────────┬────────────────────────────────────────┤
│  リクエスト     │  レスポンス                             │
│  {             │  {                                      │
│    "query":... │    "results": [...]                     │
│  }             │  }                                      │
└────────────────┴────────────────────────────────────────┘
```

### 6.3 Alpine.js コンポーネント設計

```javascript
{
  logs: [],
  total: 0,
  limit: 50,
  offset: 0,
  selectedLog: null,   // モーダル表示中のログ
  loading: false,
  error: null,

  async init() { await this.fetchLogs(); },
  async fetchLogs() { ... },
  openDetail(log) { this.selectedLog = log; },
  closeDetail() { this.selectedLog = null; },
  prettyJson(str) {
    try { return JSON.stringify(JSON.parse(str), null, 2); }
    catch { return str; }
  },
  async clearLogs() {
    if (!confirm('ログをすべて削除しますか？')) return;
    await client.clearApiLogs();
    await this.fetchLogs();
  },
  get totalPages() { return Math.ceil(this.total / this.limit); },
  get currentPage() { return Math.floor(this.offset / this.limit) + 1; },
  async prevPage() { ... },
  async nextPage() { ... },
}
```

---

## 7. 変更ファイル一覧

| ファイル | 変更種別 | 内容 |
|---------|---------|------|
| `backend/models/api_log.py` | **新規** | `ApiLog` モデル |
| `backend/models/__init__.py` | **変更** | `ApiLog` インポート追加 |
| `backend/services/api_log_service.py` | **新規** | `ApiLogService`（一覧取得・クリア） |
| `backend/api/v1/api_log.py` | **新規** | ページルート + API エンドポイント |
| `backend/api/v1/__init__.py` | **変更** | `from . import api_log` 追加 |
| `backend/connectai/client.py` | **変更** | `_log()` / `_save_log_async()` 追加、各メソッドにログ呼び出し追加 |
| `frontend/pages/api-log.html` | **新規** | ログ一覧・詳細モーダル画面 |
| `frontend/static/js/api-client.js` | **変更** | `getApiLogs()` / `clearApiLogs()` 追加 |
| `frontend/pages/dashboard.html` | **変更** | API ログへのリンク追加 |
| `migrations/versions/xxxx_add_api_logs.py` | **自動生成** | `flask db migrate` で生成 |

---

## 8. アーキテクチャ図

```
┌─────────────────────────────────────────────────────────────┐
│  リクエスト処理（メインスレッド）                              │
│                                                             │
│  Route → Service → ConnectAIClient._post()                  │
│                         │                                   │
│                    API 呼び出し完了                           │
│                         │                                   │
│                    _log() 呼び出し                           │
│                    ┌────┴────────────────────────────────┐  │
│                    │ user_id = current_user.id (取得)    │  │
│                    │ app = current_app._get_current_object│  │
│                    └────┬────────────────────────────────┘  │
│                         │ Thread.start() ← ノンブロッキング  │
│                    ← レスポンス返却（ここで処理完了）         │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  バックグラウンドスレッド                                      │
│                                                             │
│  with app.app_context():                                    │
│      ApiLog(user_id=..., ...) → db.session.commit()        │
└─────────────────────────────────────────────────────────────┘
```

---

## 9. テスト方針

既存の `backend/tests/conftest.py` のモック構成（`mock_connect_ai_*`）は `ConnectAIClient` 全体を patch するため、
ログ記録処理もまとめてモックされる。そのため既存テストへの影響はない。

新規テスト `backend/tests/test_api_log.py` で以下を検証する：

| テストケース | 内容 |
|------------|------|
| `test_get_api_logs_success` | 200 + logs / total |
| `test_get_api_logs_requires_login` | 未認証で 401 |
| `test_clear_api_logs_success` | 200 + 自ユーザーのログのみ削除 |
| `test_clear_api_logs_requires_login` | 未認証で 401 |
| `test_other_user_logs_not_visible` | 他ユーザーのログが一覧に含まれない |
