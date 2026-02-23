"""
AI アシスタント API のテスト

対象:
  - backend/api/v1/ai_assistant.py
"""
import json
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


def _parse_sse(data: bytes) -> list[dict]:
    """SSE レスポンスをパースしてイベントリストに変換する。"""
    events = []
    for chunk in data.decode().split("\n\n"):
        chunk = chunk.strip()
        if not chunk:
            continue
        event_type = ""
        data_str = ""
        for line in chunk.split("\n"):
            if line.startswith("event: "):
                event_type = line[7:]
            elif line.startswith("data: "):
                data_str = line[6:]
        if event_type and data_str:
            events.append({"type": event_type, "data": json.loads(data_str)})
    return events


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
             patch("backend.services.claude_service.stream_chat"):
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
# 正常系: SSE ストリーミング
# ---------------------------------------------------------------------------

class TestAiAssistantChat:
    def test_chat_returns_sse_stream(self, client, app):
        _register_and_login(client)
        _set_api_key(app)

        def mock_stream(api_key, jwt_token, messages, catalog_name=None):
            yield "text_delta", {"text": "テスト回答"}
            yield "done", {"message": "complete", "answer": "テスト回答"}

        with patch("backend.api.v1.ai_assistant.generate_connect_ai_jwt", return_value="tok"), \
             patch("backend.services.claude_service.stream_chat", side_effect=mock_stream):
            resp = client.post("/api/v1/ai-assistant/chat", json={"message": "カタログ一覧を教えて"})

        assert resp.status_code == 200
        assert "text/event-stream" in resp.content_type
        events = _parse_sse(resp.data)
        assert events[0] == {"type": "text_delta", "data": {"text": "テスト回答"}}
        assert events[-1]["type"] == "done"

    def test_chat_passes_catalog_name(self, client, app):
        _register_and_login(client)
        _set_api_key(app)

        captured = {}

        def mock_stream(api_key, jwt_token, messages, catalog_name=None):
            captured["catalog_name"] = catalog_name
            yield "done", {"message": "complete", "answer": "ok"}

        with patch("backend.api.v1.ai_assistant.generate_connect_ai_jwt", return_value="tok"), \
             patch("backend.services.claude_service.stream_chat", side_effect=mock_stream):
            client.post("/api/v1/ai-assistant/chat", json={
                "message": "hello",
                "catalog_name": "SalesDB",
            })

        assert captured["catalog_name"] == "SalesDB"

    def test_empty_catalog_name_passed_as_none(self, client, app):
        _register_and_login(client)
        _set_api_key(app)

        captured = {}

        def mock_stream(api_key, jwt_token, messages, catalog_name=None):
            captured["catalog_name"] = catalog_name
            yield "done", {"message": "complete", "answer": "ok"}

        with patch("backend.api.v1.ai_assistant.generate_connect_ai_jwt", return_value="tok"), \
             patch("backend.services.claude_service.stream_chat", side_effect=mock_stream):
            client.post("/api/v1/ai-assistant/chat", json={
                "message": "hello",
                "catalog_name": "",
            })

        assert captured["catalog_name"] is None

    def test_stream_error_yields_error_event(self, client, app):
        _register_and_login(client)
        _set_api_key(app)

        def mock_stream(api_key, jwt_token, messages, catalog_name=None):
            yield "error", {"error": "Anthropic API error"}

        with patch("backend.api.v1.ai_assistant.generate_connect_ai_jwt", return_value="tok"), \
             patch("backend.services.claude_service.stream_chat", side_effect=mock_stream):
            resp = client.post("/api/v1/ai-assistant/chat", json={"message": "hello"})

        assert resp.status_code == 200  # SSE エラーはイベントとして送信
        events = _parse_sse(resp.data)
        assert events[0] == {"type": "error", "data": {"error": "Anthropic API error"}}

    def test_tool_events_included_in_stream(self, client, app):
        _register_and_login(client)
        _set_api_key(app)

        def mock_stream(api_key, jwt_token, messages, catalog_name=None):
            yield "tool_start", {"tool_name": "getCatalogs", "tool_input": {}}
            yield "tool_result", {"tool_name": "getCatalogs", "result": "cat1,cat2"}
            yield "text_delta", {"text": "カタログ一覧: cat1, cat2"}
            yield "done", {"message": "complete", "answer": "カタログ一覧: cat1, cat2"}

        with patch("backend.api.v1.ai_assistant.generate_connect_ai_jwt", return_value="tok"), \
             patch("backend.services.claude_service.stream_chat", side_effect=mock_stream):
            resp = client.post("/api/v1/ai-assistant/chat", json={"message": "カタログを教えて"})

        events = _parse_sse(resp.data)
        event_types = [e["type"] for e in events]
        assert "tool_start" in event_types
        assert "tool_result" in event_types
        assert "text_delta" in event_types
        assert "done" in event_types

    def test_no_tool_events_when_no_tool_calls(self, client, app):
        _register_and_login(client)
        _set_api_key(app)

        def mock_stream(api_key, jwt_token, messages, catalog_name=None):
            yield "text_delta", {"text": "こんにちは！"}
            yield "done", {"message": "complete", "answer": "こんにちは！"}

        with patch("backend.api.v1.ai_assistant.generate_connect_ai_jwt", return_value="tok"), \
             patch("backend.services.claude_service.stream_chat", side_effect=mock_stream):
            resp = client.post("/api/v1/ai-assistant/chat", json={"message": "こんにちは"})

        events = _parse_sse(resp.data)
        event_types = [e["type"] for e in events]
        assert "tool_start" not in event_types
        assert "tool_result" not in event_types
        assert "text_delta" in event_types


# ---------------------------------------------------------------------------
# 正常系: クライアントサイド履歴
# ---------------------------------------------------------------------------

class TestAiAssistantClientHistory:
    def test_messages_merged_with_client_history(self, client, app):
        _register_and_login(client)
        _set_api_key(app)

        captured = {}

        def mock_stream(api_key, jwt_token, messages, catalog_name=None):
            captured["messages"] = list(messages)
            yield "done", {"message": "complete", "answer": "回答"}

        with patch("backend.api.v1.ai_assistant.generate_connect_ai_jwt", return_value="tok"), \
             patch("backend.services.claude_service.stream_chat", side_effect=mock_stream):
            client.post("/api/v1/ai-assistant/chat", json={
                "message": "質問2",
                "messages": [
                    {"role": "user", "content": "質問1"},
                    {"role": "assistant", "content": "回答1"},
                ],
            })

        # クライアント履歴 + 新しいメッセージが結合される
        assert len(captured["messages"]) == 3
        assert captured["messages"][0]["content"] == "質問1"
        assert captured["messages"][1]["content"] == "回答1"
        assert captured["messages"][2]["content"] == "質問2"
        assert captured["messages"][2]["role"] == "user"

    def test_no_history_sends_only_user_message(self, client, app):
        _register_and_login(client)
        _set_api_key(app)

        captured = {}

        def mock_stream(api_key, jwt_token, messages, catalog_name=None):
            captured["messages"] = list(messages)
            yield "done", {"message": "complete", "answer": "回答"}

        with patch("backend.api.v1.ai_assistant.generate_connect_ai_jwt", return_value="tok"), \
             patch("backend.services.claude_service.stream_chat", side_effect=mock_stream):
            client.post("/api/v1/ai-assistant/chat", json={"message": "初めての質問"})

        assert len(captured["messages"]) == 1
        assert captured["messages"][0]["role"] == "user"
        assert captured["messages"][0]["content"] == "初めての質問"

    def test_reset_returns_200(self, client):
        _register_and_login(client)
        resp = client.post("/api/v1/ai-assistant/reset")
        assert resp.status_code == 200
