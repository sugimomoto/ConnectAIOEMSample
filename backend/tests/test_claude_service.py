"""
Claude サービスのテスト

対象:
  - backend/services/claude_service.py
"""
import pytest
from unittest.mock import patch, MagicMock
from backend.services.claude_service import chat, _block_to_dict


# ---------------------------------------------------------------------------
# テスト用ヘルパー
# ---------------------------------------------------------------------------

class _TextBlock:
    type = "text"

    def __init__(self, text: str):
        self.text = text


class _ToolUseBlock:
    type = "tool_use"

    def __init__(self, tool_id: str, name: str, tool_input: dict):
        self.id = tool_id
        self.name = name
        self.input = tool_input


class _Response:
    def __init__(self, stop_reason: str, content: list):
        self.stop_reason = stop_reason
        self.content = content


SAMPLE_TOOLS = [
    {
        "name": "getCatalogs",
        "description": "List catalogs",
        "input_schema": {"type": "object", "properties": {}},
    }
]

SAMPLE_JWT = "test.jwt.token"
SAMPLE_API_KEY = "sk-ant-api03-test"


# ---------------------------------------------------------------------------
# _block_to_dict
# ---------------------------------------------------------------------------

class TestBlockToDict:
    def test_text_block(self):
        block = _TextBlock("Hello")
        result = _block_to_dict(block)
        assert result == {"type": "text", "text": "Hello"}

    def test_tool_use_block(self):
        block = _ToolUseBlock("tu_1", "getCatalogs", {"a": 1})
        result = _block_to_dict(block)
        assert result == {"type": "tool_use", "id": "tu_1", "name": "getCatalogs", "input": {"a": 1}}

    def test_dict_passthrough(self):
        d = {"type": "text", "text": "already a dict"}
        assert _block_to_dict(d) is d


# ---------------------------------------------------------------------------
# chat() — 正常系
# ---------------------------------------------------------------------------

class TestChatEndTurn:
    """end_turn で完了するシンプルな会話"""

    def test_returns_text_and_empty_tool_calls(self):
        mock_response = _Response("end_turn", [_TextBlock("回答テキストです。")])

        with patch("backend.services.claude_service.Anthropic") as MockAnthropic, \
             patch("backend.services.claude_service.get_mcp_tools", return_value=SAMPLE_TOOLS), \
             patch("backend.services.claude_service.MCPClient"):

            mock_client = MagicMock()
            MockAnthropic.return_value = mock_client
            mock_client.messages.create.return_value = mock_response

            answer, tool_calls = chat(SAMPLE_API_KEY, SAMPLE_JWT, [
                {"role": "user", "content": "こんにちは"}
            ])

        assert answer == "回答テキストです。"
        assert tool_calls == []

    def test_initializes_anthropic_with_api_key(self):
        mock_response = _Response("end_turn", [_TextBlock("ok")])

        with patch("backend.services.claude_service.Anthropic") as MockAnthropic, \
             patch("backend.services.claude_service.get_mcp_tools", return_value=SAMPLE_TOOLS), \
             patch("backend.services.claude_service.MCPClient"):

            mock_client = MagicMock()
            MockAnthropic.return_value = mock_client
            mock_client.messages.create.return_value = mock_response

            chat(SAMPLE_API_KEY, SAMPLE_JWT, [{"role": "user", "content": "test"}])

        MockAnthropic.assert_called_once_with(api_key=SAMPLE_API_KEY)

    def test_passes_tools_to_api(self):
        mock_response = _Response("end_turn", [_TextBlock("ok")])

        with patch("backend.services.claude_service.Anthropic") as MockAnthropic, \
             patch("backend.services.claude_service.get_mcp_tools", return_value=SAMPLE_TOOLS), \
             patch("backend.services.claude_service.MCPClient"):

            mock_client = MagicMock()
            MockAnthropic.return_value = mock_client
            mock_client.messages.create.return_value = mock_response

            chat(SAMPLE_API_KEY, SAMPLE_JWT, [{"role": "user", "content": "test"}])

        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs["tools"] == SAMPLE_TOOLS

    def test_catalog_name_added_to_system(self):
        mock_response = _Response("end_turn", [_TextBlock("ok")])

        with patch("backend.services.claude_service.Anthropic") as MockAnthropic, \
             patch("backend.services.claude_service.get_mcp_tools", return_value=SAMPLE_TOOLS), \
             patch("backend.services.claude_service.MCPClient"):

            mock_client = MagicMock()
            MockAnthropic.return_value = mock_client
            mock_client.messages.create.return_value = mock_response

            chat(SAMPLE_API_KEY, SAMPLE_JWT, [{"role": "user", "content": "test"}],
                 catalog_name="SalesDB")

        system = mock_client.messages.create.call_args[1]["system"]
        assert "SalesDB" in system

    def test_no_catalog_name_no_catalog_in_system(self):
        mock_response = _Response("end_turn", [_TextBlock("ok")])

        with patch("backend.services.claude_service.Anthropic") as MockAnthropic, \
             patch("backend.services.claude_service.get_mcp_tools", return_value=SAMPLE_TOOLS), \
             patch("backend.services.claude_service.MCPClient"):

            mock_client = MagicMock()
            MockAnthropic.return_value = mock_client
            mock_client.messages.create.return_value = mock_response

            chat(SAMPLE_API_KEY, SAMPLE_JWT, [{"role": "user", "content": "test"}])

        system = mock_client.messages.create.call_args[1]["system"]
        assert "カタログ" not in system

    def test_multiple_text_blocks_joined(self):
        mock_response = _Response("end_turn", [
            _TextBlock("Part 1"),
            _TextBlock("Part 2"),
        ])

        with patch("backend.services.claude_service.Anthropic") as MockAnthropic, \
             patch("backend.services.claude_service.get_mcp_tools", return_value=SAMPLE_TOOLS), \
             patch("backend.services.claude_service.MCPClient"):

            mock_client = MagicMock()
            MockAnthropic.return_value = mock_client
            mock_client.messages.create.return_value = mock_response

            answer, _ = chat(SAMPLE_API_KEY, SAMPLE_JWT, [{"role": "user", "content": "test"}])

        assert answer == "Part 1\nPart 2"


# ---------------------------------------------------------------------------
# chat() — ツール呼び出しフロー
# ---------------------------------------------------------------------------

class TestChatToolUse:
    """tool_use → MCP 呼び出し → end_turn のループ"""

    def _setup_tool_use_then_end_turn(self, mock_client, mcp_result: str = "cat1,cat2"):
        """1回の tool_use の後に end_turn するシナリオをセットアップ"""
        tool_response = _Response(
            "tool_use",
            [
                _TextBlock("ツールを呼び出します"),
                _ToolUseBlock("tu_001", "getCatalogs", {}),
            ],
        )
        final_response = _Response("end_turn", [_TextBlock("カタログ一覧: cat1, cat2")])
        mock_client.messages.create.side_effect = [tool_response, final_response]
        return mcp_result

    def test_tool_use_returns_answer_and_tool_calls_log(self):
        with patch("backend.services.claude_service.Anthropic") as MockAnthropic, \
             patch("backend.services.claude_service.get_mcp_tools", return_value=SAMPLE_TOOLS), \
             patch("backend.services.claude_service.MCPClient") as MockMCPClient:

            mock_client = MagicMock()
            MockAnthropic.return_value = mock_client
            self._setup_tool_use_then_end_turn(mock_client)

            mock_mcp = MagicMock()
            MockMCPClient.return_value = mock_mcp
            mock_mcp.call_tool.return_value = "cat1,cat2"

            answer, tool_calls = chat(SAMPLE_API_KEY, SAMPLE_JWT, [
                {"role": "user", "content": "カタログ一覧を教えて"}
            ])

        assert answer == "カタログ一覧: cat1, cat2"
        assert len(tool_calls) == 1
        assert tool_calls[0]["name"] == "getCatalogs"
        assert tool_calls[0]["input"] == {}
        assert tool_calls[0]["result"] == "cat1,cat2"

    def test_mcp_call_tool_called_with_correct_args(self):
        with patch("backend.services.claude_service.Anthropic") as MockAnthropic, \
             patch("backend.services.claude_service.get_mcp_tools", return_value=SAMPLE_TOOLS), \
             patch("backend.services.claude_service.MCPClient") as MockMCPClient:

            mock_client = MagicMock()
            MockAnthropic.return_value = mock_client
            self._setup_tool_use_then_end_turn(mock_client)

            mock_mcp = MagicMock()
            MockMCPClient.return_value = mock_mcp
            mock_mcp.call_tool.return_value = "result"

            chat(SAMPLE_API_KEY, SAMPLE_JWT, [{"role": "user", "content": "test"}])

        mock_mcp.call_tool.assert_called_once_with("getCatalogs", {})

    def test_mcp_error_recorded_in_tool_calls(self):
        from backend.services.mcp_client import MCPError

        with patch("backend.services.claude_service.Anthropic") as MockAnthropic, \
             patch("backend.services.claude_service.get_mcp_tools", return_value=SAMPLE_TOOLS), \
             patch("backend.services.claude_service.MCPClient") as MockMCPClient:

            mock_client = MagicMock()
            MockAnthropic.return_value = mock_client
            self._setup_tool_use_then_end_turn(mock_client)

            mock_mcp = MagicMock()
            MockMCPClient.return_value = mock_mcp
            mock_mcp.call_tool.side_effect = MCPError("Connection refused")

            _, tool_calls = chat(SAMPLE_API_KEY, SAMPLE_JWT, [{"role": "user", "content": "test"}])

        assert "エラー" in tool_calls[0]["result"]
        assert "Connection refused" in tool_calls[0]["result"]

    def test_tool_result_sent_back_to_claude(self):
        with patch("backend.services.claude_service.Anthropic") as MockAnthropic, \
             patch("backend.services.claude_service.get_mcp_tools", return_value=SAMPLE_TOOLS), \
             patch("backend.services.claude_service.MCPClient") as MockMCPClient:

            mock_client = MagicMock()
            MockAnthropic.return_value = mock_client
            self._setup_tool_use_then_end_turn(mock_client)

            mock_mcp = MagicMock()
            MockMCPClient.return_value = mock_mcp
            mock_mcp.call_tool.return_value = "cat1,cat2"

            chat(SAMPLE_API_KEY, SAMPLE_JWT, [{"role": "user", "content": "test"}])

        # 2回目の messages.create 呼び出しを確認
        assert mock_client.messages.create.call_count == 2
        second_call_messages = mock_client.messages.create.call_args_list[1][1]["messages"]

        # tool_result が含まれることを確認
        user_with_tool_result = second_call_messages[-1]
        assert user_with_tool_result["role"] == "user"
        tool_result_content = user_with_tool_result["content"]
        assert isinstance(tool_result_content, list)
        assert tool_result_content[0]["type"] == "tool_result"
        assert tool_result_content[0]["tool_use_id"] == "tu_001"
        assert tool_result_content[0]["content"] == "cat1,cat2"


# ---------------------------------------------------------------------------
# chat() — 会話履歴
# ---------------------------------------------------------------------------

class TestChatHistory:
    def test_history_passed_to_messages_create(self):
        mock_response = _Response("end_turn", [_TextBlock("ok")])

        with patch("backend.services.claude_service.Anthropic") as MockAnthropic, \
             patch("backend.services.claude_service.get_mcp_tools", return_value=SAMPLE_TOOLS), \
             patch("backend.services.claude_service.MCPClient"):

            mock_client = MagicMock()
            MockAnthropic.return_value = mock_client
            mock_client.messages.create.return_value = mock_response

            history = [
                {"role": "user", "content": "最初の質問"},
                {"role": "assistant", "content": "最初の回答"},
                {"role": "user", "content": "2回目の質問"},
            ]
            chat(SAMPLE_API_KEY, SAMPLE_JWT, history)

        messages = mock_client.messages.create.call_args[1]["messages"]
        assert len(messages) == 3
        assert messages[0]["content"] == "最初の質問"
        assert messages[1]["content"] == "最初の回答"
        assert messages[2]["content"] == "2回目の質問"
