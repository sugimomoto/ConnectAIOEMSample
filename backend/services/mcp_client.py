import uuid
import requests

MCP_BASE_URL = "https://mcp.cloud.cdata.com/mcp"

_cached_tools: list[dict] | None = None


class MCPError(Exception):
    """MCP サーバーとの通信エラー"""


class MCPClient:
    """
    CData Connect AI MCP クライアント。
    Streamable HTTP (JSON-RPC 2.0) で MCP サーバーと通信する。
    jwt_token の sub クレームがテナント分離に使われる。
    """

    def __init__(self, jwt_token: str) -> None:
        self.jwt_token = jwt_token

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.jwt_token}",
            "Content-Type": "application/json",
        }

    def _call_jsonrpc(self, method: str, params: dict) -> dict:
        """
        JSON-RPC 2.0 リクエストを MCP サーバーに送信し、result を返す。

        Raises:
            MCPError: HTTP エラー・JSON-RPC エラー・接続エラー時
        """
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": str(uuid.uuid4()),
        }
        try:
            resp = requests.post(
                MCP_BASE_URL,
                json=payload,
                headers=self._headers(),
                timeout=60,
            )
            resp.raise_for_status()
        except requests.HTTPError as e:
            raise MCPError(
                f"HTTP {e.response.status_code}: {e.response.text[:500]}"
            ) from e
        except requests.RequestException as e:
            raise MCPError(f"Request failed: {e}") from e

        try:
            body = resp.json()
        except Exception as e:
            raise MCPError(
                f"Invalid JSON response: {resp.text[:500]!r}"
            ) from e

        if "error" in body:
            err = body["error"]
            raise MCPError(
                f"JSON-RPC error {err.get('code')}: {err.get('message')}"
            )

        return body.get("result", {})

    @staticmethod
    def _to_anthropic_format(mcp_tool: dict) -> dict:
        """MCP ツール定義を Anthropic SDK の tools 形式に変換する。"""
        return {
            "name": mcp_tool["name"],
            "description": mcp_tool.get("description", ""),
            "input_schema": mcp_tool["inputSchema"],
        }

    def list_tools(self) -> list[dict]:
        """
        MCP サーバーからツール定義一覧を取得し、Anthropic 形式に変換して返す。

        Returns:
            [{"name": "...", "description": "...", "input_schema": {...}}, ...]
        """
        result = self._call_jsonrpc("tools/list", {})
        mcp_tools = result.get("tools", [])
        return [self._to_anthropic_format(t) for t in mcp_tools]

    def call_tool(self, tool_name: str, tool_input: dict) -> str:
        """
        指定したツールを呼び出し、テキスト結果を返す。

        Returns:
            ツール実行結果のテキスト
        Raises:
            MCPError: 呼び出し失敗時
        """
        result = self._call_jsonrpc(
            "tools/call",
            {"name": tool_name, "arguments": tool_input},
        )
        content = result.get("content", [])
        texts = [
            block["text"]
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        ]
        return "\n".join(texts)


# ---------------------------------------------------------------------------
# モジュールレベル: ツール定義キャッシュ
# ---------------------------------------------------------------------------

def get_mcp_tools(jwt_token: str) -> list[dict]:
    """
    MCP ツール定義を返す（初回のみ取得してキャッシュ）。

    Args:
        jwt_token: MCP サーバー認証用 JWT
    Returns:
        Anthropic 形式のツール定義リスト
    """
    global _cached_tools
    if _cached_tools is None:
        client = MCPClient(jwt_token)
        _cached_tools = client.list_tools()
    return _cached_tools


def invalidate_tools_cache() -> None:
    """ツール定義キャッシュを破棄する（テスト・再読み込み用）。"""
    global _cached_tools
    _cached_tools = None


# ---------------------------------------------------------------------------
# モジュールレベル: 個別ツール呼び出し（Flask コンテキスト依存）
# ---------------------------------------------------------------------------

def _make_client(account_id: str) -> MCPClient:
    """account_id から JWT を生成して MCPClient を作成する（Flask コンテキスト必要）。"""
    from flask import current_app
    from backend.connectai.jwt import generate_connect_ai_jwt

    parent_id = current_app.config["CONNECT_AI_PARENT_ACCOUNT_ID"]
    jwt_token = generate_connect_ai_jwt(parent_id, account_id)
    return MCPClient(jwt_token)


def get_catalogs(account_id: str) -> str:
    """カタログ一覧を取得して CSV 文字列で返す。"""
    return _make_client(account_id).call_tool("getCatalogs", {})


def get_schemas(account_id: str, catalog_name: str) -> str:
    """スキーマ一覧を取得して CSV 文字列で返す。"""
    return _make_client(account_id).call_tool(
        "getSchemas", {"catalogName": catalog_name}
    )


def get_tables(account_id: str, catalog_name: str, schema_name: str) -> str:
    """テーブル一覧を取得して CSV 文字列で返す。"""
    return _make_client(account_id).call_tool(
        "getTables", {"catalogName": catalog_name, "schemaName": schema_name}
    )


def get_columns(
    account_id: str, catalog_name: str, schema_name: str, table_name: str
) -> str:
    """カラム一覧を取得して CSV 文字列で返す。"""
    return _make_client(account_id).call_tool(
        "getColumns",
        {
            "catalogName": catalog_name,
            "schemaName": schema_name,
            "tableName": table_name,
        },
    )


def query_data(
    account_id: str, query: str, parameters: dict | None = None
) -> str:
    """SQL クエリを実行して CSV 文字列で返す。"""
    tool_input: dict = {"query": query}
    if parameters:
        tool_input["parameters"] = parameters
    return _make_client(account_id).call_tool("queryData", tool_input)
