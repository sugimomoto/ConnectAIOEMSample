"""
MCP クライアントのテスト

対象:
  - backend/services/mcp_client.py
  - MCPClient クラスの各メソッド
  - get_mcp_tools() / invalidate_tools_cache() モジュール関数
"""
import json
import pytest
from unittest.mock import patch, MagicMock
from backend.services.mcp_client import (
    MCPClient,
    MCPError,
    get_mcp_tools,
    invalidate_tools_cache,
)


# ---------------------------------------------------------------------------
# テスト用フィクスチャ・定数
# ---------------------------------------------------------------------------

SAMPLE_JWT = "test.jwt.token"
MCP_URL = "https://mcp.cloud.cdata.com/mcp"

SAMPLE_MCP_TOOLS = [
    {
        "name": "getCatalogs",
        "description": "List available catalogs",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "queryData",
        "description": "Execute SQL query",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "SQL query"},
            },
            "required": ["query"],
        },
    },
]

SAMPLE_ANTHROPIC_TOOLS = [
    {
        "name": "getCatalogs",
        "description": "List available catalogs",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "queryData",
        "description": "Execute SQL query",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "SQL query"},
            },
            "required": ["query"],
        },
    },
]


def _make_jsonrpc_response(result: dict) -> MagicMock:
    """正常な JSON-RPC 2.0 レスポンスを模倣した Mock を返す。"""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"jsonrpc": "2.0", "result": result, "id": "1"}
    mock_resp.raise_for_status.return_value = None
    return mock_resp


def _make_jsonrpc_error_response(code: int, message: str) -> MagicMock:
    """JSON-RPC エラーレスポンスを模倣した Mock を返す。"""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "jsonrpc": "2.0",
        "error": {"code": code, "message": message},
        "id": "1",
    }
    mock_resp.raise_for_status.return_value = None
    return mock_resp


# ---------------------------------------------------------------------------
# MCPClient._to_anthropic_format
# ---------------------------------------------------------------------------

class TestToAnthropicFormat:
    """MCP → Anthropic フォーマット変換のテスト"""

    def test_converts_inputSchema_to_input_schema(self):
        mcp_tool = {
            "name": "queryData",
            "description": "Run SQL",
            "inputSchema": {"type": "object", "properties": {}},
        }
        result = MCPClient._to_anthropic_format(mcp_tool)
        assert result["name"] == "queryData"
        assert result["description"] == "Run SQL"
        assert "input_schema" in result
        assert "inputSchema" not in result
        assert result["input_schema"] == {"type": "object", "properties": {}}

    def test_missing_description_defaults_to_empty_string(self):
        mcp_tool = {
            "name": "getCatalogs",
            "inputSchema": {"type": "object"},
        }
        result = MCPClient._to_anthropic_format(mcp_tool)
        assert result["description"] == ""

    def test_preserves_input_schema_structure(self):
        schema = {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer"},
            },
            "required": ["query"],
        }
        mcp_tool = {"name": "x", "inputSchema": schema}
        result = MCPClient._to_anthropic_format(mcp_tool)
        assert result["input_schema"] == schema


# ---------------------------------------------------------------------------
# MCPClient.list_tools
# ---------------------------------------------------------------------------

class TestListTools:
    """list_tools のテスト"""

    def test_returns_anthropic_formatted_tools(self):
        mock_resp = _make_jsonrpc_response({"tools": SAMPLE_MCP_TOOLS})
        with patch("requests.post", return_value=mock_resp) as mock_post:
            client = MCPClient(SAMPLE_JWT)
            tools = client.list_tools()

        assert tools == SAMPLE_ANTHROPIC_TOOLS
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        assert call_kwargs[0][0] == MCP_URL
        payload = call_kwargs[1]["json"]
        assert payload["method"] == "tools/list"

    def test_sends_bearer_auth_header(self):
        mock_resp = _make_jsonrpc_response({"tools": []})
        with patch("requests.post", return_value=mock_resp) as mock_post:
            MCPClient(SAMPLE_JWT).list_tools()

        headers = mock_post.call_args[1]["headers"]
        assert headers["Authorization"] == f"Bearer {SAMPLE_JWT}"

    def test_empty_tools_returns_empty_list(self):
        mock_resp = _make_jsonrpc_response({"tools": []})
        with patch("requests.post", return_value=mock_resp):
            tools = MCPClient(SAMPLE_JWT).list_tools()
        assert tools == []

    def test_raises_mcp_error_on_jsonrpc_error(self):
        mock_resp = _make_jsonrpc_error_response(-32600, "Invalid Request")
        with patch("requests.post", return_value=mock_resp):
            with pytest.raises(MCPError, match="JSON-RPC error"):
                MCPClient(SAMPLE_JWT).list_tools()

    def test_raises_mcp_error_on_http_error(self):
        import requests as _requests
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.text = "Unauthorized"
        http_error = _requests.HTTPError(response=mock_resp)
        mock_resp.raise_for_status.side_effect = http_error

        with patch("requests.post", return_value=mock_resp):
            with pytest.raises(MCPError, match="HTTP 401"):
                MCPClient(SAMPLE_JWT).list_tools()

    def test_raises_mcp_error_on_connection_error(self):
        import requests as _requests
        with patch(
            "requests.post",
            side_effect=_requests.ConnectionError("Connection refused"),
        ):
            with pytest.raises(MCPError, match="Request failed"):
                MCPClient(SAMPLE_JWT).list_tools()


# ---------------------------------------------------------------------------
# MCPClient.call_tool
# ---------------------------------------------------------------------------

class TestCallTool:
    """call_tool のテスト"""

    def test_returns_text_content(self):
        mock_resp = _make_jsonrpc_response(
            {
                "content": [
                    {"type": "text", "text": "catalog1,catalog2"},
                ]
            }
        )
        with patch("requests.post", return_value=mock_resp):
            result = MCPClient(SAMPLE_JWT).call_tool("getCatalogs", {})
        assert result == "catalog1,catalog2"

    def test_joins_multiple_text_blocks(self):
        mock_resp = _make_jsonrpc_response(
            {
                "content": [
                    {"type": "text", "text": "first"},
                    {"type": "text", "text": "second"},
                ]
            }
        )
        with patch("requests.post", return_value=mock_resp):
            result = MCPClient(SAMPLE_JWT).call_tool("getCatalogs", {})
        assert result == "first\nsecond"

    def test_ignores_non_text_blocks(self):
        mock_resp = _make_jsonrpc_response(
            {
                "content": [
                    {"type": "image", "data": "..."},
                    {"type": "text", "text": "csv data"},
                ]
            }
        )
        with patch("requests.post", return_value=mock_resp):
            result = MCPClient(SAMPLE_JWT).call_tool("queryData", {"query": "SELECT 1"})
        assert result == "csv data"

    def test_sends_correct_jsonrpc_payload(self):
        mock_resp = _make_jsonrpc_response({"content": []})
        with patch("requests.post", return_value=mock_resp) as mock_post:
            MCPClient(SAMPLE_JWT).call_tool("queryData", {"query": "SELECT 1"})

        payload = mock_post.call_args[1]["json"]
        assert payload["method"] == "tools/call"
        assert payload["params"]["name"] == "queryData"
        assert payload["params"]["arguments"] == {"query": "SELECT 1"}

    def test_empty_content_returns_empty_string(self):
        mock_resp = _make_jsonrpc_response({"content": []})
        with patch("requests.post", return_value=mock_resp):
            result = MCPClient(SAMPLE_JWT).call_tool("getCatalogs", {})
        assert result == ""

    def test_raises_mcp_error_on_jsonrpc_error(self):
        mock_resp = _make_jsonrpc_error_response(-32000, "Tool execution failed")
        with patch("requests.post", return_value=mock_resp):
            with pytest.raises(MCPError, match="JSON-RPC error"):
                MCPClient(SAMPLE_JWT).call_tool("getCatalogs", {})

    def test_raises_mcp_error_on_http_403(self):
        import requests as _requests
        mock_resp = MagicMock()
        mock_resp.status_code = 403
        mock_resp.text = "Forbidden"
        mock_resp.raise_for_status.side_effect = _requests.HTTPError(response=mock_resp)

        with patch("requests.post", return_value=mock_resp):
            with pytest.raises(MCPError, match="HTTP 403"):
                MCPClient(SAMPLE_JWT).call_tool("getCatalogs", {})


# ---------------------------------------------------------------------------
# get_mcp_tools / invalidate_tools_cache
# ---------------------------------------------------------------------------

class TestGetMcpTools:
    """get_mcp_tools / invalidate_tools_cache のテスト"""

    def setup_method(self):
        """各テスト前にキャッシュをクリアする。"""
        invalidate_tools_cache()

    def test_returns_tools_on_first_call(self):
        mock_resp = _make_jsonrpc_response({"tools": SAMPLE_MCP_TOOLS})
        with patch("requests.post", return_value=mock_resp):
            tools = get_mcp_tools(SAMPLE_JWT)
        assert tools == SAMPLE_ANTHROPIC_TOOLS

    def test_caches_result_and_calls_api_only_once(self):
        mock_resp = _make_jsonrpc_response({"tools": SAMPLE_MCP_TOOLS})
        with patch("requests.post", return_value=mock_resp) as mock_post:
            get_mcp_tools(SAMPLE_JWT)
            get_mcp_tools(SAMPLE_JWT)
            get_mcp_tools(SAMPLE_JWT)

        assert mock_post.call_count == 1

    def test_invalidate_clears_cache(self):
        mock_resp = _make_jsonrpc_response({"tools": SAMPLE_MCP_TOOLS})
        with patch("requests.post", return_value=mock_resp) as mock_post:
            get_mcp_tools(SAMPLE_JWT)
            invalidate_tools_cache()
            get_mcp_tools(SAMPLE_JWT)

        assert mock_post.call_count == 2

    def test_returns_same_object_from_cache(self):
        mock_resp = _make_jsonrpc_response({"tools": SAMPLE_MCP_TOOLS})
        with patch("requests.post", return_value=mock_resp):
            first = get_mcp_tools(SAMPLE_JWT)
            second = get_mcp_tools(SAMPLE_JWT)
        assert first is second
