import json
from typing import Generator

from anthropic import Anthropic
from backend.services.mcp_client import MCPClient, MCPError, get_mcp_tools


_SYSTEM_PROMPT = (
    "あなたは CData Connect AI を通じてデータにアクセスできるデータアナリストアシスタントです。"
    "ユーザーの質問に答えるために、提供されているツールを使ってデータを取得・分析してください。"
    "回答は日本語で行ってください。"
)

_MAX_ITERATIONS = 10


def _block_to_dict(block) -> dict:
    """Anthropic SDK のコンテンツブロックを JSON シリアライズ可能な dict に変換する。"""
    if isinstance(block, dict):
        return block
    d: dict = {"type": block.type}
    if block.type == "text":
        d["text"] = block.text
    elif block.type == "tool_use":
        d["id"] = block.id
        d["name"] = block.name
        d["input"] = dict(block.input)
    return d


def chat(
    api_key: str,
    jwt_token: str,
    messages: list[dict],
    catalog_name: str | None = None,
) -> tuple[str, list[dict]]:
    """
    Agentic ループを実行し、最終的なテキスト回答とツール呼び出しログを返す。

    Args:
        api_key: ユーザーの Claude API Key
        jwt_token: Connect AI MCP 認証用 JWT（sub クレーム = accountId）
        messages: 会話履歴（{"role": "user"/"assistant", "content": str} のリスト）
        catalog_name: 優先カタログ名（省略時は Claude が自律的に探索する）

    Returns:
        (answer, tool_calls) tuple
        - answer: Claude の最終回答テキスト
        - tool_calls: [{"name": str, "input": dict, "result": str}, ...]
    """
    client = Anthropic(api_key=api_key)
    mcp = MCPClient(jwt_token)
    tools = get_mcp_tools(jwt_token)

    system = _SYSTEM_PROMPT
    if catalog_name:
        system += f"\n優先して使用するカタログ名は '{catalog_name}' です。"

    # messages はセッション保存用の plain dict（テキストのみ）から開始する
    current_messages: list[dict] = [
        {"role": m["role"], "content": m["content"]} for m in messages
    ]
    tool_calls_log: list[dict] = []

    for _ in range(_MAX_ITERATIONS):
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=4096,
            system=system,
            messages=current_messages,
            tools=tools,
        )

        if response.stop_reason == "end_turn":
            text_parts = [b.text for b in response.content if b.type == "text"]
            return "\n".join(text_parts), tool_calls_log

        if response.stop_reason == "tool_use":
            # アシスタントのレスポンス（tool_use ブロック含む）をメッセージに追加
            current_messages.append({
                "role": "assistant",
                "content": [_block_to_dict(b) for b in response.content],
            })

            # 各ツールを MCP 経由で実行
            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                try:
                    result = mcp.call_tool(block.name, block.input)
                except MCPError as e:
                    result = f"エラー: {e}"

                tool_calls_log.append({
                    "name": block.name,
                    "input": dict(block.input),
                    "result": result,
                })
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

            current_messages.append({"role": "user", "content": tool_results})
            continue

        # 予期しない stop_reason（max_tokens など）
        break

    return "", tool_calls_log


def stream_chat(
    api_key: str,
    jwt_token: str,
    messages: list[dict],
    catalog_name: str | None = None,
) -> Generator[tuple[str, dict], None, None]:
    """
    Agentic ループをストリーミングで実行し、SSE イベントを (event_type, data) として yield する。

    Yields:
        ("text_delta",  {"text": "..."})
        ("tool_start",  {"tool_name": "...", "tool_input": {...}})
        ("tool_result", {"tool_name": "...", "result": "..."})
        ("done",        {"message": "complete", "answer": "..."})
        ("error",       {"error": "..."})  ← 例外発生時
    """
    client = Anthropic(api_key=api_key)
    mcp = MCPClient(jwt_token)
    tools = get_mcp_tools(jwt_token)

    system = _SYSTEM_PROMPT
    if catalog_name:
        system += f"\n優先して使用するカタログ名は '{catalog_name}' です。"

    current_messages: list[dict] = [
        {"role": m["role"], "content": m["content"]} for m in messages
    ]
    full_answer_parts: list[str] = []

    try:
        for _ in range(_MAX_ITERATIONS):
            with client.messages.stream(
                model="claude-opus-4-6",
                max_tokens=4096,
                system=system,
                messages=current_messages,
                tools=tools,
            ) as stream:
                for text in stream.text_stream:
                    yield "text_delta", {"text": text}
                    full_answer_parts.append(text)

                final_message = stream.get_final_message()

            if final_message.stop_reason == "end_turn":
                break

            if final_message.stop_reason == "tool_use":
                current_messages.append({
                    "role": "assistant",
                    "content": [_block_to_dict(b) for b in final_message.content],
                })

                tool_results = []
                for block in final_message.content:
                    if block.type != "tool_use":
                        continue
                    yield "tool_start", {
                        "tool_name": block.name,
                        "tool_input": dict(block.input),
                    }
                    try:
                        result = mcp.call_tool(block.name, block.input)
                    except MCPError as e:
                        result = f"エラー: {e}"

                    yield "tool_result", {"tool_name": block.name, "result": result}
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })

                current_messages.append({"role": "user", "content": tool_results})
                continue

            break

    except Exception as e:
        yield "error", {"error": str(e)}
        return

    yield "done", {"message": "complete", "answer": "".join(full_answer_parts)}
