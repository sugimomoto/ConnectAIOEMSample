# MCP API

## 概要

CData Connect AI の MCP（Model Context Protocol）サーバーは、AI アプリケーションと外部データソースを接続するための Anthropic 標準プロトコルを実装したエンドポイントです。

AI モデル（Claude など）から自然言語でデータに問い合わせると、MCP サーバーがデータソースへの接続・クエリ実行・結果返却を仲介します。

### MCPサーバーURL

```
https://mcp.cloud.cdata.com/mcp
```

### プロトコル

**Streamable HTTP**（MCP over HTTP）を使用します。WebSocket や SSE ではなく、HTTP リクエスト/レスポンスで MCP メッセージをやり取りします。

---

## 認証

本アプリケーションでは **OAuth JWT Bearer Token 認証**のみをサポートします。

### OAuth（JWT Bearer Token）認証

OEM 構成（Powered-by API）の JWT トークンを使用します。

```http
Authorization: Bearer {JWT_TOKEN}
```

JWT トークンの `sub` クレームに子アカウントの `accountId` を設定することで、テナント分離も同時に実現されます。

JWT トークンの生成方法は [認証ドキュメント](./authentication.md) を参照してください。

---

## 利用可能なツール

MCP サーバーは以下の 8 つのツールを提供します。AI モデルはこれらのツールを自律的に選択・呼び出してデータにアクセスします。

### 1. getCatalogs

利用可能な接続（カタログ）の一覧を取得します。

**入力パラメータ：** なし

**説明：** ユーザーアカウントに登録されているすべてのデータソース接続を返します。

---

### 2. getSchemas

指定したカタログのスキーマ一覧を取得します。

**入力パラメータ：**

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `catalogName` | string | ○ | 対象のカタログ（コネクション）名 |

---

### 3. getTables

指定したカタログ・スキーマのテーブル一覧を取得します。

**入力パラメータ：**

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `catalogName` | string | ○ | 対象のカタログ名 |
| `schemaName` | string | ○ | 対象のスキーマ名 |

---

### 4. getColumns

テーブルのカラム構造と定義を取得します。

**入力パラメータ：**

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `catalogName` | string | ○ | 対象のカタログ名 |
| `schemaName` | string | ○ | 対象のスキーマ名 |
| `tableName` | string | ○ | 対象のテーブル名 |

---

### 5. queryData

データソースに対して SQL クエリを実行し、結果を取得します。

**入力パラメータ：**

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `query` | string | ○ | 実行する SELECT 文（SQL-92 標準） |
| `parameters` | object | × | `@param_name` 形式のパラメータ値 |
| `schemaOnly` | boolean | × | スキーマ情報のみ返す（デフォルト: false） |

**SQL構文の注意事項：**
- 識別子（テーブル名・カラム名）は `[]` でクォートする
- ブール値は `1`（TRUE）/ `0`（FALSE）を使用
- サポートされる句: `SELECT`, `FROM`, `WHERE`, `INNER JOIN`, `LEFT JOIN`, `GROUP BY`, `HAVING`, `ORDER BY`, `LIMIT`/`OFFSET`

**完全修飾テーブル参照形式：**
```sql
SELECT * FROM [CatalogName].[SchemaName].[TableName]
```

---

### 6. getProcedures

指定したカタログ・スキーマのストアドプロシージャ一覧を取得します。

**入力パラメータ：**

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `catalogName` | string | ○ | 対象のカタログ名 |
| `schemaName` | string | ○ | 対象のスキーマ名 |

---

### 7. getProcedureParameters

ストアドプロシージャの実行に必要なパラメータ（名前・データ型・方向）を取得します。

**入力パラメータ：**

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `catalogName` | string | ○ | 対象のカタログ名 |
| `schemaName` | string | ○ | 対象のスキーマ名 |
| `procedureName` | string | ○ | 対象のプロシージャ名 |

---

### 8. executeProcedure

ストアドプロシージャを実行します。

**入力パラメータ：**

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `catalogName` | string | ○ | 対象のカタログ名 |
| `schemaName` | string | ○ | 対象のスキーマ名 |
| `procedureName` | string | ○ | 実行するプロシージャ名 |
| `parameters` | object | × | プロシージャのパラメータ（`@param_name: value` 形式） |

---

## バックエンドからの接続方法（Python / Streamable HTTP）

Claude Code / Anthropic Python SDK を使ってバックエンドから MCP サーバーに接続する場合、Streamable HTTP トランスポートを使用します。

### claude mcp add コマンド（CLI接続設定）

```bash
claude mcp add --transport http connectmcp \
  https://mcp.cloud.cdata.com/mcp \
  --header "Authorization: Bearer {JWT_TOKEN}"
```

### Python（Anthropic SDK）での利用例

Anthropic Python SDK のツール使用機能を通じて MCP ツールを呼び出します。MCP サーバーへの直接接続はバックエンドが担当し、Claude API にはツール定義（`tools` パラメータ）を渡します。

```python
import anthropic
import requests

client = anthropic.Anthropic(api_key="ユーザーのAPI Key")

MCP_BASE_URL = "https://mcp.cloud.cdata.com/mcp"

# Claude に渡す MCP ツール定義
MCP_TOOLS = [
    {
        "name": "getCatalogs",
        "description": "利用可能なコネクション（カタログ）一覧を取得する",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "getSchemas",
        "description": "指定カタログのスキーマ一覧を取得する",
        "input_schema": {
            "type": "object",
            "properties": {
                "catalogName": {"type": "string", "description": "カタログ名"}
            },
            "required": ["catalogName"]
        }
    },
    {
        "name": "getTables",
        "description": "指定カタログ・スキーマのテーブル一覧を取得する",
        "input_schema": {
            "type": "object",
            "properties": {
                "catalogName": {"type": "string"},
                "schemaName": {"type": "string"}
            },
            "required": ["catalogName", "schemaName"]
        }
    },
    {
        "name": "getColumns",
        "description": "指定テーブルのカラム一覧を取得する",
        "input_schema": {
            "type": "object",
            "properties": {
                "catalogName": {"type": "string"},
                "schemaName": {"type": "string"},
                "tableName": {"type": "string"}
            },
            "required": ["catalogName", "schemaName", "tableName"]
        }
    },
    {
        "name": "queryData",
        "description": "SQL クエリを実行してデータを取得する",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "実行する SELECT 文"},
                "parameters": {
                    "type": "object",
                    "description": "@param 形式のパラメータ値"
                }
            },
            "required": ["query"]
        }
    }
]

def call_mcp_tool(tool_name: str, tool_input: dict, jwt_token: str) -> str:
    """バックエンドから MCP ツールを Streamable HTTP で呼び出す"""
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json"
    }
    # MCP JSON-RPC リクエスト形式
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": tool_input
        },
        "id": 1
    }
    response = requests.post(MCP_BASE_URL, json=payload, headers=headers)
    return response.json()

def chat_with_mcp(user_message: str, jwt_token: str) -> str:
    """自然言語の質問を受け取り、MCP を使ってデータにアクセスして回答する"""
    messages = [{"role": "user", "content": user_message}]

    # Agentic loop: Claude がツール呼び出しを止めるまで繰り返す
    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            tools=MCP_TOOLS,
            messages=messages
        )

        if response.stop_reason == "end_turn":
            # 最終回答を返す
            return next(b.text for b in response.content if b.type == "text")

        if response.stop_reason == "tool_use":
            # ツール呼び出しを処理
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = call_mcp_tool(block.name, block.input, jwt_token)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(result)
                    })
            messages.append({"role": "user", "content": tool_results})
```

---

## テナント分離（OEM構成）

Embedded Cloud（OEM）構成では、JWT トークンの `sub` クレームに子アカウントの `accountId` を設定することでテナント分離を実現します。各ユーザーは自分のアカウントに紐づいたコネクションのみにアクセスできます。

詳細は [認証ドキュメント](./authentication.md) を参照してください。

---

## 参考リンク

- [CData Connect AI MCP 公式ドキュメント](https://docs.cloud.cdata.com/en/API/MCP)
- [Embedded Cloud MCP ドキュメント](https://docs.cloud.cdata.com/en/API/MCP-Embedded.md)
- [Claude Code + Connect AI MCP 接続ガイド](https://docs.cloud.cdata.com/en/Clients/ClaudeCode-Client-Embedded.md)

---

[← トップに戻る](./README.md)
