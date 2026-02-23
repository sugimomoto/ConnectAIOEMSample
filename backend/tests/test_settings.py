"""
設定 API のテスト（テストファースト）

対象:
  - backend/services/crypto_service.py（Fernet 暗号化ユーティリティ）
  - backend/api/v1/settings.py（API Key 保存・削除・状態確認）
"""
import pytest
from cryptography.fernet import Fernet
from backend.models import db
from backend.models.user import User


# ---------------------------------------------------------------------------
# ヘルパー
# ---------------------------------------------------------------------------

def _register_and_login(client, email="user@example.com", password="password123", name="Test User"):
    client.post("/api/v1/auth/register", json={"email": email, "password": password, "name": name})
    client.post("/api/v1/auth/login", json={"email": email, "password": password})


# ---------------------------------------------------------------------------
# crypto_service
# ---------------------------------------------------------------------------

class TestCryptoService:
    """Fernet 暗号化ユーティリティのユニットテスト"""

    def test_encrypt_returns_different_string(self, app):
        """encrypt した値は平文とは異なる文字列であること"""
        with app.app_context():
            from backend.services.crypto_service import encrypt
            plaintext = "sk-ant-api03-testkey"
            encrypted = encrypt(plaintext)
            assert encrypted != plaintext

    def test_decrypt_roundtrip(self, app):
        """encrypt → decrypt で元の平文に戻ること"""
        with app.app_context():
            from backend.services.crypto_service import encrypt, decrypt
            plaintext = "sk-ant-api03-testkey"
            assert decrypt(encrypt(plaintext)) == plaintext

    def test_decrypt_with_wrong_key_raises_value_error(self, app):
        """異なるキーで復号しようとすると ValueError が発生すること"""
        with app.app_context():
            from backend.services.crypto_service import encrypt
            encrypted = encrypt("sk-ant-api03-testkey")

        # 別のキーを持つアプリコンテキストで復号を試みる
        from backend.app import create_app
        app2 = create_app({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-key",
            "ENCRYPTION_KEY": Fernet.generate_key().decode(),  # 別キー
        })
        with app2.app_context():
            from backend.services.crypto_service import decrypt
            with pytest.raises(ValueError):
                decrypt(encrypted)

    def test_encrypt_without_key_raises_runtime_error(self, app):
        """ENCRYPTION_KEY が未設定の場合 RuntimeError が発生すること"""
        from backend.app import create_app
        app_no_key = create_app({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-key",
            "ENCRYPTION_KEY": "",
        })
        with app_no_key.app_context():
            from backend.services.crypto_service import encrypt
            with pytest.raises(RuntimeError, match="ENCRYPTION_KEY"):
                encrypt("sk-ant-api03-testkey")


# ---------------------------------------------------------------------------
# 設定 API - 認証保護
# ---------------------------------------------------------------------------

class TestSettingsAuth:
    """未ログイン時のアクセス制御テスト"""

    def test_get_status_without_login_returns_401(self, client):
        resp = client.get("/api/v1/settings/api-key/status")
        assert resp.status_code == 401

    def test_save_api_key_without_login_returns_401(self, client):
        resp = client.post("/api/v1/settings/api-key", json={"api_key": "sk-ant-api03-test"})
        assert resp.status_code == 401

    def test_delete_api_key_without_login_returns_401(self, client):
        resp = client.delete("/api/v1/settings/api-key")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# 設定 API - API Key 状態確認
# ---------------------------------------------------------------------------

class TestApiKeyStatus:
    """GET /api/v1/settings/api-key/status"""

    def test_status_returns_false_when_no_key(self, client):
        """API Key 未登録時は has_api_key: false が返ること"""
        _register_and_login(client)
        resp = client.get("/api/v1/settings/api-key/status")
        assert resp.status_code == 200
        assert resp.get_json()["has_api_key"] is False

    def test_status_returns_true_after_saving_key(self, client):
        """API Key 保存後は has_api_key: true が返ること"""
        _register_and_login(client)
        client.post("/api/v1/settings/api-key", json={"api_key": "sk-ant-api03-testkey"})
        resp = client.get("/api/v1/settings/api-key/status")
        assert resp.status_code == 200
        assert resp.get_json()["has_api_key"] is True


# ---------------------------------------------------------------------------
# 設定 API - API Key 保存
# ---------------------------------------------------------------------------

class TestSaveApiKey:
    """POST /api/v1/settings/api-key"""

    def test_save_valid_key_returns_200(self, client):
        """有効な API Key を保存すると 200 が返ること"""
        _register_and_login(client)
        resp = client.post("/api/v1/settings/api-key", json={"api_key": "sk-ant-api03-testkey"})
        assert resp.status_code == 200

    def test_save_key_stores_encrypted_value_in_db(self, client, app):
        """API Key が DB に暗号化されて保存されること（平文ではないこと）"""
        _register_and_login(client)
        client.post("/api/v1/settings/api-key", json={"api_key": "sk-ant-api03-testkey"})
        with app.app_context():
            user = db.session.query(User).filter_by(email="user@example.com").first()
            assert user.claude_api_key_encrypted is not None
            assert user.claude_api_key_encrypted != "sk-ant-api03-testkey"

    def test_save_key_can_be_decrypted_back(self, client, app):
        """保存された暗号化 API Key を復号すると元の値に戻ること"""
        _register_and_login(client)
        original_key = "sk-ant-api03-testkey"
        client.post("/api/v1/settings/api-key", json={"api_key": original_key})
        with app.app_context():
            from backend.services.crypto_service import decrypt
            user = db.session.query(User).filter_by(email="user@example.com").first()
            assert decrypt(user.claude_api_key_encrypted) == original_key

    def test_save_empty_key_returns_400(self, client):
        """空文字の API Key では 400 が返ること"""
        _register_and_login(client)
        resp = client.post("/api/v1/settings/api-key", json={"api_key": ""})
        assert resp.status_code == 400

    def test_save_invalid_format_key_returns_400(self, client):
        """sk-ant- で始まらない API Key では 400 が返ること"""
        _register_and_login(client)
        resp = client.post("/api/v1/settings/api-key", json={"api_key": "invalid-key-format"})
        assert resp.status_code == 400

    def test_save_key_overwrites_existing_key(self, client, app):
        """2回目の保存で API Key が上書きされること"""
        _register_and_login(client)
        client.post("/api/v1/settings/api-key", json={"api_key": "sk-ant-api03-first"})
        client.post("/api/v1/settings/api-key", json={"api_key": "sk-ant-api03-second"})
        with app.app_context():
            from backend.services.crypto_service import decrypt
            user = db.session.query(User).filter_by(email="user@example.com").first()
            assert decrypt(user.claude_api_key_encrypted) == "sk-ant-api03-second"


# ---------------------------------------------------------------------------
# 設定 API - API Key 削除
# ---------------------------------------------------------------------------

class TestDeleteApiKey:
    """DELETE /api/v1/settings/api-key"""

    def test_delete_key_returns_200(self, client):
        """API Key 削除が 200 を返すこと"""
        _register_and_login(client)
        client.post("/api/v1/settings/api-key", json={"api_key": "sk-ant-api03-testkey"})
        resp = client.delete("/api/v1/settings/api-key")
        assert resp.status_code == 200

    def test_delete_key_clears_db_value(self, client, app):
        """削除後に DB の claude_api_key_encrypted が NULL になること"""
        _register_and_login(client)
        client.post("/api/v1/settings/api-key", json={"api_key": "sk-ant-api03-testkey"})
        client.delete("/api/v1/settings/api-key")
        with app.app_context():
            user = db.session.query(User).filter_by(email="user@example.com").first()
            assert user.claude_api_key_encrypted is None

    def test_status_returns_false_after_deletion(self, client):
        """削除後に has_api_key: false になること"""
        _register_and_login(client)
        client.post("/api/v1/settings/api-key", json={"api_key": "sk-ant-api03-testkey"})
        client.delete("/api/v1/settings/api-key")
        resp = client.get("/api/v1/settings/api-key/status")
        assert resp.get_json()["has_api_key"] is False


# ---------------------------------------------------------------------------
# ユーザー分離
# ---------------------------------------------------------------------------

class TestApiKeyIsolation:
    """API Key がユーザーごとに分離されること"""

    def test_two_users_have_independent_api_keys(self, client, second_user_client):
        """ユーザー A の API Key 保存がユーザー B に影響しないこと"""
        # client を別ユーザーとして登録・ログイン（second_user_client は "other@example.com" で設定済み）
        client.post("/api/v1/auth/register", json={"email": "user-a@example.com", "password": "pass123", "name": "User A"})
        client.post("/api/v1/auth/login", json={"email": "user-a@example.com", "password": "pass123"})

        client.post("/api/v1/settings/api-key", json={"api_key": "sk-ant-api03-user-a"})

        # second_user_client（other@example.com）は API Key を持たないまま
        resp = second_user_client.get("/api/v1/settings/api-key/status")
        assert resp.get_json()["has_api_key"] is False

    def test_user_cannot_access_another_users_key(self, client, second_user_client, app):
        """ユーザー A と B がそれぞれ異なる暗号化値を持つこと"""
        client.post("/api/v1/auth/register", json={"email": "user-a@example.com", "password": "pass123", "name": "User A"})
        client.post("/api/v1/auth/login", json={"email": "user-a@example.com", "password": "pass123"})

        client.post("/api/v1/settings/api-key", json={"api_key": "sk-ant-api03-user-a"})
        second_user_client.post("/api/v1/settings/api-key", json={"api_key": "sk-ant-api03-user-b"})

        with app.app_context():
            from backend.services.crypto_service import decrypt
            user_a = db.session.query(User).filter_by(email="user-a@example.com").first()
            user_b = db.session.query(User).filter_by(email="other@example.com").first()
            assert decrypt(user_a.claude_api_key_encrypted) == "sk-ant-api03-user-a"
            assert decrypt(user_b.claude_api_key_encrypted) == "sk-ant-api03-user-b"
