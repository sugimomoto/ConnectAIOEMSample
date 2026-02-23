"""
API ログ機能のテスト（テストファースト）
"""
import pytest
from backend.models.api_log import ApiLog
from backend.models import db


# ---------------------------------------------------------------------------
# ヘルパー
# ---------------------------------------------------------------------------

def _register_and_login(client, email="user@example.com", password="password123", name="Test User"):
    client.post("/api/v1/auth/register", json={"email": email, "password": password, "name": name})
    client.post("/api/v1/auth/login", json={"email": email, "password": password})


def _insert_log(app, user_id: int, endpoint: str = "/query", method: str = "POST",
                status_code: int = 200, elapsed_ms: int = 100):
    """テスト用ログレコードを直接 DB に挿入するヘルパー"""
    with app.app_context():
        log = ApiLog(
            user_id=user_id,
            method=method,
            endpoint=endpoint,
            request_body='{"query": "SELECT * FROM Account"}',
            response_body='{"results": []}',
            status_code=status_code,
            elapsed_ms=elapsed_ms,
        )
        db.session.add(log)
        db.session.commit()


def _get_user_id(app, email: str) -> int:
    """メールアドレスからユーザー ID を取得するヘルパー"""
    with app.app_context():
        from backend.models.user import User
        return User.query.filter_by(email=email).first().id


# ---------------------------------------------------------------------------
# API テスト
# ---------------------------------------------------------------------------

def test_get_api_logs_success(app, client):
    """ログイン済みユーザーが自分のログ一覧を取得できること"""
    _register_and_login(client)
    user_id = _get_user_id(app, "user@example.com")
    _insert_log(app, user_id, endpoint="/query")
    _insert_log(app, user_id, endpoint="/catalogs")

    resp = client.get("/api/v1/api-logs")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "logs" in data
    assert "total" in data
    assert data["total"] == 2
    assert len(data["logs"]) == 2
    log = data["logs"][0]
    assert "id" in log
    assert "timestamp" in log
    assert "method" in log
    assert "endpoint" in log
    assert "status_code" in log
    assert "elapsed_ms" in log
    assert "request_body" in log
    assert "response_body" in log


def test_get_api_logs_requires_login(client):
    """未認証でのログ一覧取得は 401 が返ること"""
    resp = client.get("/api/v1/api-logs")
    assert resp.status_code == 401


def test_clear_api_logs_success(app, client):
    """ログイン済みユーザーが自分のログを全件削除できること"""
    _register_and_login(client)
    user_id = _get_user_id(app, "user@example.com")
    _insert_log(app, user_id)
    _insert_log(app, user_id)

    resp = client.delete("/api/v1/api-logs")
    assert resp.status_code == 200

    resp = client.get("/api/v1/api-logs")
    data = resp.get_json()
    assert data["total"] == 0
    assert len(data["logs"]) == 0


def test_clear_api_logs_requires_login(client):
    """未認証でのログ削除は 401 が返ること"""
    resp = client.delete("/api/v1/api-logs")
    assert resp.status_code == 401


def test_other_user_logs_not_visible(app, client):
    """他ユーザーのログは自分の一覧に含まれないこと"""
    # ユーザー1・ユーザー2 を登録（ログインなし）
    client.post("/api/v1/auth/register", json={
        "email": "user1@example.com", "password": "password123", "name": "User1"
    })
    client.post("/api/v1/auth/register", json={
        "email": "user2@example.com", "password": "password123", "name": "User2"
    })
    user1_id = _get_user_id(app, "user1@example.com")
    user2_id = _get_user_id(app, "user2@example.com")

    # 各ユーザーのログを DB に直接挿入
    _insert_log(app, user1_id, endpoint="/query")
    _insert_log(app, user2_id, endpoint="/catalogs")

    # ユーザー1 でログインして取得 → user1 のログのみ見える
    client.post("/api/v1/auth/login", json={
        "email": "user1@example.com", "password": "password123"
    })
    resp = client.get("/api/v1/api-logs")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["total"] == 1
    assert data["logs"][0]["endpoint"] == "/query"
