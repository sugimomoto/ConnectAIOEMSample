"""
AI アシスタント API のテスト

対象:
  - backend/api/v1/ai_assistant.py
"""
import pytest
from unittest.mock import patch
from cryptography.fernet import Fernet
from backend.models import db
from backend.models.user import User
from backend.services import crypto_service


# ---------------------------------------------------------------------------
# ヘルパー
# ---------------------------------------------------------------------------

def _register_and_login(client, email="user@example.com", password="password123", name="Test User"):
    client.post("/api/v1/auth/register", json={"email": email, "password": password, "name": name})
    client.post("/api/v1/auth/login", json={"email": email, "password": password})


def _set_api_key(app, email="user@example.com"):
    """テスト用ユーザーに暗号化済み API Key を設定する。"""
    with app.app_context():
        user = db.session.query(User).filter_by(email=email).first()
        user.claude_api_key_encrypted = crypto_service.encrypt("sk-ant-api03-test-key")
        db.session.commit()


# ---------------------------------------------------------------------------
# 認証チェック
# ---------------------------------------------------------------------------

class TestAiAssistantAuth:
    def test_chat_without_login_returns_401(self, client):
        resp = client.post("/api/v1/ai-assistant/chat", json={"message": "hello"})
        assert resp.status_code == 401

    def test_reset_without_login_returns_401(self, client):
        resp = client.post("/api/v1/ai-assistant/reset")
        assert resp.status_code == 401

    def test_page_without_login_redirects(self, client):
        resp = client.get("/ai-assistant")
        # Flask-Login redirects to login page
        assert resp.status_code in (302, 401)


# ---------------------------------------------------------------------------
# バリデーション
# ---------------------------------------------------------------------------

class TestAiAssistantValidation:
    def test_empty_message_returns_400(self, client, app):
        _register_and_login(client)
        _set_api_key(app)
        with patch("backend.api.v1.ai_assistant.generate_connect_ai_jwt", return_value="tok"), \
             patch("backend.services.claude_service.chat"):
            resp = client.post("/api/v1/ai-assistant/chat", json={"message": "  "})
        assert resp.status_code == 400
        assert resp.get_json()["error"]["code"] == "VALIDATION_ERROR"

    def test_missing_message_returns_400(self, client, app):
        _register_and_login(client)
        _set_api_key(app)
        resp = client.post("/api/v1/ai-assistant/chat", json={})
        assert resp.status_code == 400

    def test_no_api_key_returns_422(self, client):
        _register_and_login(client)
        resp = client.post("/api/v1/ai-assistant/chat", json={"message": "hello"})
        assert resp.status_code == 422
        assert resp.get_json()["error"]["code"] == "NO_API_KEY"


# ---------------------------------------------------------------------------
# 正常系: チャット
# ---------------------------------------------------------------------------

class TestAiAssistantChat:
    def test_chat_returns_answer_and_tool_calls(self, client, app):
        _register_and_login(client)
        _set_api_key(app)

        with patch("backend.api.v1.ai_assistant.generate_connect_ai_jwt", return_value="tok"), \
             patch("backend.services.claude_service.chat",
                   return_value=("テスト回答", [{"name": "getCatalogs", "input": {}, "result": "cat1"}])):
            resp = client.post("/api/v1/ai-assistant/chat", json={"message": "カタログ一覧を教えて"})

        assert resp.status_code == 200
        data = resp.get_json()
        assert data["answer"] == "テスト回答"
        assert len(data["tool_calls"]) == 1
        assert data["tool_calls"][0]["name"] == "getCatalogs"

    def test_chat_passes_catalog_name(self, client, app):
        _register_and_login(client)
        _set_api_key(app)

        captured = {}
        def mock_chat(api_key, jwt_token, messages, catalog_name=None):
            captured["catalog_name"] = catalog_name
            return ("ok", [])

        with patch("backend.api.v1.ai_assistant.generate_connect_ai_jwt", return_value="tok"), \
             patch("backend.services.claude_service.chat", side_effect=mock_chat):
            client.post("/api/v1/ai-assistant/chat", json={
                "message": "hello",
                "catalog_name": "SalesDB",
            })

        assert captured["catalog_name"] == "SalesDB"

    def test_empty_catalog_name_passed_as_none(self, client, app):
        _register_and_login(client)
        _set_api_key(app)

        captured = {}
        def mock_chat(api_key, jwt_token, messages, catalog_name=None):
            captured["catalog_name"] = catalog_name
            return ("ok", [])

        with patch("backend.api.v1.ai_assistant.generate_connect_ai_jwt", return_value="tok"), \
             patch("backend.services.claude_service.chat", side_effect=mock_chat):
            client.post("/api/v1/ai-assistant/chat", json={
                "message": "hello",
                "catalog_name": "",
            })

        assert captured["catalog_name"] is None

    def test_claude_error_returns_500(self, client, app):
        _register_and_login(client)
        _set_api_key(app)

        with patch("backend.api.v1.ai_assistant.generate_connect_ai_jwt", return_value="tok"), \
             patch("backend.services.claude_service.chat",
                   side_effect=Exception("Anthropic API error")):
            resp = client.post("/api/v1/ai-assistant/chat", json={"message": "hello"})

        assert resp.status_code == 500
        assert resp.get_json()["error"]["code"] == "CLAUDE_ERROR"


# ---------------------------------------------------------------------------
# 正常系: セッション管理
# ---------------------------------------------------------------------------

class TestAiAssistantSession:
    def test_chat_history_accumulated_in_session(self, client, app):
        _register_and_login(client)
        _set_api_key(app)

        call_count = 0
        received_histories = []

        def mock_chat(api_key, jwt_token, messages, catalog_name=None):
            nonlocal call_count
            call_count += 1
            received_histories.append(list(messages))
            return (f"回答{call_count}", [])

        with patch("backend.api.v1.ai_assistant.generate_connect_ai_jwt", return_value="tok"), \
             patch("backend.services.claude_service.chat", side_effect=mock_chat):
            client.post("/api/v1/ai-assistant/chat", json={"message": "質問1"})
            client.post("/api/v1/ai-assistant/chat", json={"message": "質問2"})

        # 2回目の呼び出しには前の会話が含まれる
        second_call_messages = received_histories[1]
        assert len(second_call_messages) == 3  # user, assistant, user
        assert second_call_messages[0]["content"] == "質問1"
        assert second_call_messages[1]["content"] == "回答1"
        assert second_call_messages[2]["content"] == "質問2"

    def test_reset_clears_session(self, client, app):
        _register_and_login(client)
        _set_api_key(app)

        received_histories = []

        def mock_chat(api_key, jwt_token, messages, catalog_name=None):
            received_histories.append(list(messages))
            return ("回答", [])

        with patch("backend.api.v1.ai_assistant.generate_connect_ai_jwt", return_value="tok"), \
             patch("backend.services.claude_service.chat", side_effect=mock_chat):
            client.post("/api/v1/ai-assistant/chat", json={"message": "質問1"})
            client.post("/api/v1/ai-assistant/reset")
            client.post("/api/v1/ai-assistant/chat", json={"message": "質問2"})

        # リセット後の呼び出しは履歴なし（最初のメッセージのみ）
        third_call_messages = received_histories[1]
        assert len(third_call_messages) == 1
        assert third_call_messages[0]["content"] == "質問2"

    def test_reset_returns_200(self, client):
        _register_and_login(client)
        resp = client.post("/api/v1/ai-assistant/reset")
        assert resp.status_code == 200
