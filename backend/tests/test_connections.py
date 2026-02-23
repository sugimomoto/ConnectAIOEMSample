"""
コネクション管理 API のテスト（テストファースト）

各テストは実装前に記述しているため、実装完了前は FAIL する。
"""
import pytest


# ---------------------------------------------------------------------------
# ヘルパー
# ---------------------------------------------------------------------------

def _register_and_login(client, email="user@example.com", password="password123", name="Test User"):
    """ユーザーを登録してログインし、セッションを確立する"""
    client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "name": name,
    })
    client.post("/api/v1/auth/login", json={
        "email": email,
        "password": password,
    })


def _register_and_login_no_child_account(client, app):
    """connect_ai_account_id が NULL のユーザーを登録してログインする"""
    from unittest.mock import patch
    from backend.models import db
    from backend.models.user import User

    # connect_ai_account_id が設定されないようにモックを上書き
    with patch("backend.connectai.client.ConnectAIClient.create_account") as mock:
        mock.return_value = None
        client.post("/api/v1/auth/register", json={
            "email": "nochildaccount@example.com",
            "password": "password123",
            "name": "No Child Account User",
        })

    # DBを直接更新してNULLにする
    with app.app_context():
        user = db.session.query(User).filter_by(email="nochildaccount@example.com").first()
        user.connect_ai_account_id = None
        db.session.commit()

    client.post("/api/v1/auth/login", json={
        "email": "nochildaccount@example.com",
        "password": "password123",
    })


# ---------------------------------------------------------------------------
# データソース一覧取得
# ---------------------------------------------------------------------------

def test_get_datasources_success(client, mock_connect_ai_connections):
    """ログイン済みユーザーがデータソース一覧を取得できること"""
    _register_and_login(client)
    resp = client.get("/api/v1/datasources")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "datasources" in data
    assert len(data["datasources"]) == 2
    assert data["datasources"][0]["name"] == "Salesforce"
    assert data["datasources"][1]["name"] == "QuickBooks"


def test_get_datasources_requires_login(client, mock_connect_ai_connections):
    """未認証でのデータソース取得は 401 が返ること"""
    resp = client.get("/api/v1/datasources")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# コネクション一覧取得
# ---------------------------------------------------------------------------

def test_get_connections_success(client, mock_connect_ai_connections):
    """ログイン済みユーザーがコネクション一覧を取得できること"""
    _register_and_login(client)
    resp = client.get("/api/v1/connections")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "connections" in data
    assert len(data["connections"]) == 1
    assert data["connections"][0]["id"] == "conn-001"
    assert data["connections"][0]["name"] == "My SF"
    assert data["connections"][0]["dataSource"] == "Salesforce"
    assert data["connections"][0]["status"] == "active"


def test_get_connections_requires_login(client, mock_connect_ai_connections):
    """未認証でのコネクション一覧取得は 401 が返ること"""
    resp = client.get("/api/v1/connections")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# コネクション作成
# ---------------------------------------------------------------------------

def test_create_connection_success(client, mock_connect_ai_connections):
    """正常なコネクション作成で 201 と redirectURL が返ること"""
    _register_and_login(client)
    resp = client.post("/api/v1/connections", json={
        "name": "My Salesforce",
        "data_source": "Salesforce",
    })
    assert resp.status_code == 201
    data = resp.get_json()
    assert "redirectURL" in data
    assert data["redirectURL"] == "https://cloud.cdata.com/connect/auth/mock-token"


def test_create_connection_without_child_account(client, app, mock_connect_ai_connections):
    """connect_ai_account_id が未設定のユーザーがコネクション作成すると 403 が返ること"""
    _register_and_login_no_child_account(client, app)
    resp = client.post("/api/v1/connections", json={
        "name": "My Salesforce",
        "data_source": "Salesforce",
    })
    assert resp.status_code == 403


def test_create_connection_requires_login(client, mock_connect_ai_connections):
    """未認証でのコネクション作成は 401 が返ること"""
    resp = client.post("/api/v1/connections", json={
        "name": "My Salesforce",
        "data_source": "Salesforce",
    })
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# コネクション削除
# ---------------------------------------------------------------------------

def test_delete_connection_success(client, mock_connect_ai_connections):
    """正常なコネクション削除で 200 が返ること"""
    _register_and_login(client)
    resp = client.delete("/api/v1/connections/conn-001")
    assert resp.status_code == 200
    mock_connect_ai_connections["delete"].assert_called_once_with("conn-001")


def test_delete_connection_requires_login(client, mock_connect_ai_connections):
    """未認証でのコネクション削除は 401 が返ること"""
    resp = client.delete("/api/v1/connections/conn-001")
    assert resp.status_code == 401
