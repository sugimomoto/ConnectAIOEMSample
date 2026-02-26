"""
認証 API のテスト（テストファースト）

各テストは実装前に記述しているため、実装完了前は FAIL する。
"""
import pytest
from backend.models import db
from backend.models.user import User


# ---------------------------------------------------------------------------
# ヘルパー
# ---------------------------------------------------------------------------

def _register(client, email="user@example.com", password="password123", name="Test User"):
    return client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "name": name,
    })


def _login(client, email="user@example.com", password="password123"):
    return client.post("/api/v1/auth/login", json={
        "email": email,
        "password": password,
    })


# ---------------------------------------------------------------------------
# ユーザー登録
# ---------------------------------------------------------------------------

def test_register_success(client):
    """正常なユーザー登録で 201 と user オブジェクトが返ること"""
    resp = _register(client)
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["user"]["email"] == "user@example.com"
    assert data["user"]["name"] == "Test User"
    assert "id" in data["user"]


def test_register_duplicate_email_returns_409(client):
    """同じメールアドレスで2回登録すると 409 が返ること"""
    _register(client)
    resp = _register(client)
    assert resp.status_code == 409


def test_register_saves_child_account_id(client, app):
    """登録後に connect_ai_account_id（ChildAccountId）がDBに保存されること"""
    _register(client)
    with app.app_context():
        user = db.session.query(User).filter_by(email="user@example.com").first()
        assert user is not None
        assert user.connect_ai_account_id == "mock-child-account-id-001"


def test_register_uses_email_as_external_id(client, mock_connect_ai):
    """externalId としてメールアドレスが Connect AI API に渡されること"""
    _register(client, email="user@example.com")
    mock_connect_ai.assert_called_once_with("user@example.com")


def test_register_password_is_hashed(client, app):
    """パスワードが平文でなくbcryptハッシュとしてDBに保存されること"""
    _register(client, password="mysecretpass")
    with app.app_context():
        user = db.session.query(User).filter_by(email="user@example.com").first()
        assert user is not None
        assert user.password_hash != "mysecretpass"
        # bcrypt ハッシュは "$2b$" で始まる
        assert user.password_hash.startswith("$2b$")


# ---------------------------------------------------------------------------
# ログイン
# ---------------------------------------------------------------------------

def test_login_success(client):
    """正常なログインで 200 と user オブジェクトが返ること"""
    _register(client)
    resp = _login(client)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["user"]["email"] == "user@example.com"


def test_login_wrong_password_returns_401(client):
    """パスワードが一致しない場合 401 が返ること"""
    _register(client)
    resp = _login(client, password="wrongpassword")
    assert resp.status_code == 401


def test_login_unknown_email_returns_401(client):
    """登録されていないメールアドレスでログインすると 401 が返ること"""
    resp = _login(client, email="nobody@example.com")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# 認証保護
# ---------------------------------------------------------------------------

def test_protected_api_without_login_returns_401(client):
    """未ログイン状態で保護 API にアクセスすると 401 が返ること"""
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# ログアウト
# ---------------------------------------------------------------------------

def test_logout_destroys_session(client):
    """ログアウト後に保護 API にアクセスすると 401 が返ること"""
    _register(client)
    _login(client)

    # ログアウト
    resp = client.post("/api/v1/auth/logout")
    assert resp.status_code == 200

    # ログアウト後は me エンドポイントが 401 を返す
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401
