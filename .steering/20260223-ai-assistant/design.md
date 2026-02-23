# 設計書: Phase 4 - AI アシスタント機能

**作成日**: 2026-02-23
**対応Issue**: [#11](https://github.com/sugimomoto/ConnectAIOEMSample/issues/11)

---

## 実装アプローチ

### アーキテクチャ概要

```
[ブラウザ]
    │  SSE ストリーミング / REST API
    ▼
[Flask バックエンド]
    │  Anthropic Python SDK（ツール使用）
    │  ユーザーの Claude API Key を使用
    ▼
[Claude API]
    │  ツール呼び出し（MCP ツール定義）
    ▼
[Flask バックエンド] ← MCPクライアントとして動作
    │  Streamable HTTP（MCP over HTTP）
    │  Authorization: Bearer {JWT_TOKEN}
    │  JWT sub = accountId（テナント分離）
    ▼
[CData Connect AI MCP サーバー]
    https://mcp.cloud.cdata.com/mcp
```

### 通信フロー

1. ユーザーがチャット画面でメッセージ送信（カタログ選択済みの場合はカタログIDも送信）
2. バックエンドがユーザーの Claude API Key を DB から取得
3. バックエンドが Anthropic SDK でメッセージを送信（MCPツールをツール定義として渡す）
4. Claude がツール呼び出しを要求（例: `getTables`）
5. バックエンドが Connect AI MCP サーバーを呼び出し、結果を Claude に返す
6. Claude が最終回答を生成
7. SSE でフロントエンドにストリーミング送信

---

## 変更するコンポーネント

### 新規追加

| ファイル | 役割 |
|--------|------|
| `backend/routes/ai_assistant.py` | チャット API エンドポイント（SSE ストリーミング） |
| `backend/routes/settings.py` | Claude API Key 設定エンドポイント |
| `backend/services/mcp_client.py` | CData Connect AI MCP クライアント |
| `backend/services/claude_service.py` | Claude API 呼び出しサービス（ツール使用） |
| `frontend/templates/ai_assistant.html` | AIアシスタントチャット画面 |
| `frontend/templates/settings.html` | ユーザー設定画面（APIキー管理） |

### 変更する既存ファイル

| ファイル | 変更内容 |
|--------|---------|
| `backend/models.py` | `User` モデルに `claude_api_key`（暗号化）カラム追加 |
| `backend/app.py` | 新規 Blueprint の登録 |
| `frontend/templates/base.html` | ナビゲーションに「AIアシスタント」「設定」メニュー追加 |
| `backend/config.py` | 暗号化キー設定の追加 |
| `requirements.txt` | `anthropic`, `cryptography` パッケージ追加 |

---

## データ構造の変更

### User モデルへのカラム追加

```python
# backend/models.py
class User(db.Model, UserMixin):
    # 既存フィールド...
    claude_api_key_encrypted = db.Column(db.Text, nullable=True)
    # claude_api_key は暗号化して保存（Fernet 対称暗号）
```

### チャット履歴（セッション管理）

会話履歴はサーバーサイドのセッション（Flask session）で管理する。
DBへの永続化は今回のスコープ外とする。

```python
# セッション構造
session['chat_history'] = [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."},
    # tool_use / tool_result メッセージも含む
]
```

---

## MCP ツール定義

### 動的取得方式の採用

ツール定義は **MCP サーバーから動的に取得** する。

ハードコーディングではなく MCP 標準の `tools/list` メソッドを呼び出し、取得したツール定義を Claude の `tools` パラメータとして渡す。

**メリット：**
- MCP サーバー側でツールが追加・変更されても自動で追従できる
- 静的な定義ファイル（`mcp_tools.py`）の管理が不要
- 常に最新のツールスキーマを利用できる

### tools/list の呼び出し

MCP の JSON-RPC で `tools/list` メソッドを呼び出す：

```python
# mcp_client.py
def list_tools(self, jwt_token: str) -> list[dict]:
    """MCP サーバーからツール定義一覧を取得し、Anthropic 形式に変換して返す"""
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/list",
        "params": {},
        "id": 1
    }
    response = requests.post(MCP_BASE_URL, json=payload, headers={"Authorization": f"Bearer {jwt_token}"})
    mcp_tools = response.json()["result"]["tools"]
    return [self._convert_to_anthropic_format(t) for t in mcp_tools]
```

### フォーマット変換（MCP → Anthropic）

MCP と Anthropic SDK でキー名が異なる。`inputSchema`（camelCase）→ `input_schema`（snake_case）に変換が必要。

```python
def _convert_to_anthropic_format(self, mcp_tool: dict) -> dict:
    return {
        "name": mcp_tool["name"],
        "description": mcp_tool.get("description", ""),
        "input_schema": mcp_tool["inputSchema"]
    }
```

### キャッシュ戦略

ツール定義は MCP サーバー起動中は変わらないため、アプリケーション起動時に一度取得してインメモリにキャッシュする。

```python
# app.py 起動時 or claude_service.py の初期化時
_cached_tools: list[dict] | None = None

def get_mcp_tools(jwt_token: str) -> list[dict]:
    global _cached_tools
    if _cached_tools is None:
        _cached_tools = mcp_client.list_tools(jwt_token)
    return _cached_tools
```

> **注意**: キャッシュはアプリ再起動でリセットされる。ツール定義の変更を反映するにはアプリ再起動が必要（現フェーズはこれで十分）。

---

## フロントエンド設計

### AIアシスタント画面（`ai_assistant.html`）

```
┌──────────────────────────────────────────────┐
│  AI アシスタント                              │
│  カタログ: [-- 選択してください ▼]  [新しい会話] │
├──────────────────────────────────────────────┤
│  ┌────────────────────────────────────────┐  │
│  │ アシスタント                           │  │
│  │ こんにちは！データについて何でも聞いて  │  │
│  │ ください。                             │  │
│  └────────────────────────────────────────┘  │
│                                              │
│  ┌────────────────────────────────────────┐  │
│  │ ユーザー                               │  │
│  │ 売上上位10件を教えて                   │  │
│  └────────────────────────────────────────┘  │
│                                              │
│  ┌────────────────────────────────────────┐  │
│  │ アシスタント                           │  │
│  │ ▶ ツール呼び出し (3件) ← アコーディオン│  │
│  │   - getTables: SalesDB/dbo             │  │
│  │   - getColumns: Orders                 │  │
│  │   - queryData: SELECT TOP 10 ...       │  │
│  │                                        │  │
│  │ 売上上位10件は以下の通りです：         │  │
│  │ | 顧客名 | 金額 | ...                  │  │
│  └────────────────────────────────────────┘  │
├──────────────────────────────────────────────┤
│  [質問を入力...]                    [送信]    │
└──────────────────────────────────────────────┘
```

### 設定画面（`settings.html`）

```
┌──────────────────────────────────────┐
│  ユーザー設定                         │
├──────────────────────────────────────┤
│  Claude API Key                      │
│  [sk-ant-••••••••••••••••] [更新]    │
│  ※ API Key は暗号化して保存されます   │
└──────────────────────────────────────┘
```

---

## SSE ストリーミング設計

### 選択理由

AIアシスタントAPIのストリーミング方式として **SSE（Server-Sent Events）** を採用する。

| 方式 | 実装難易度 | UX | 採用理由 |
|------|-----------|-----|---------|
| **SSE** ✅ | 中 | 良い | Flask 標準機能のみ。一方向で AI チャットに最適 |
| WebSocket | 高 | 良い | 双方向通信は不要。Flask-SocketIO 等の追加依存が必要 |
| Long Polling | 低 | 悪い | チャンク単位の遅延があり UX が劣る |
| 通常 HTTP | 低 | 普通 | Phase 4-3 で動作確認用として先行実装。デモ品質には不十分 |

SSE を選択した主な理由：
- AI レスポンスはサーバー→クライアントの **一方向** のため双方向通信は不要
- Flask の `stream_with_context` + `yield` で **追加ライブラリ不要**
- ブラウザネイティブの `EventSource` API で Alpine.js から容易に利用可能
- OEM デモとして「トークンが流れてくる」視覚効果が効果的

### 段階的実装方針

Phase 4-3 で非ストリーミング版を先に実装し、動作確認後に Phase 4-4 で SSE に切り替える。

```
Phase 4-3: POST /api/v1/ai-assistant/chat → JSON レスポンス（全文一括）
           ↓ 動作確認
Phase 4-4: POST /api/v1/ai-assistant/chat → text/event-stream（SSE）
```

### SSE エンドポイント仕様

```
POST /api/v1/ai-assistant/chat
Content-Type: application/json

Response: text/event-stream
```

リクエストボディ:
```json
{
  "message": "ユーザーの質問文",
  "catalog_name": "SalesDB"  // 省略可（選択なしの場合）
}
```

### SSE イベント形式

各イベントは `event:` と `data:` フィールドで構成する。

```
event: <イベント種別>
data: <JSON文字列>

```

#### イベント種別一覧

| イベント名 | 発生タイミング | data の内容 |
|-----------|--------------|------------|
| `text_delta` | Claude のテキストトークン受信時 | `{"text": "..."}` |
| `tool_start` | Claude がツール呼び出しを要求した時 | `{"tool_name": "queryData", "tool_input": {...}}` |
| `tool_result` | MCP ツールの実行結果を受け取った時 | `{"tool_name": "queryData", "result": "..."}` |
| `done` | 全ストリーミング完了時 | `{"message": "complete"}` |
| `error` | エラー発生時 | `{"error": "エラーメッセージ"}` |

#### SSE イベントシーケンス例

```
event: tool_start
data: {"tool_name": "getTables", "tool_input": {"catalogName": "SalesDB", "schemaName": "dbo"}}

event: tool_result
data: {"tool_name": "getTables", "result": "Orders, Customers, ..."}

event: tool_start
data: {"tool_name": "queryData", "tool_input": {"query": "SELECT TOP 10 ..."}}

event: tool_result
data: {"tool_name": "queryData", "result": "顧客名,金額\nA社,100000\n..."}

event: text_delta
data: {"text": "売上"}

event: text_delta
data: {"text": "上位"}

event: text_delta
data: {"text": "10件は"}

... （以降トークンごとに繰り返し）

event: done
data: {"message": "complete"}
```

### アジェンティックループと SSE の対応

```
[Anthropic SDK stream()]
    │
    ├─ on_text_delta  ──→ SSE: text_delta
    │
    └─ stop_reason == "tool_use"
            │
            ├─ 各ツール呼び出し前 ──→ SSE: tool_start
            │
            ├─ MCP サーバー呼び出し
            │
            ├─ 結果受け取り後 ──→ SSE: tool_result
            │
            └─ 次ループ（Claude に結果を返して再度 stream()）
                    │
                    └─ stop_reason == "end_turn"
                            │
                            └─ SSE: done
```

### Flask バックエンド実装パターン

```python
# backend/routes/ai_assistant.py
from flask import Response, stream_with_context
import json

@ai_assistant_bp.route('/chat', methods=['POST'])
@login_required
def chat():
    def generate():
        for event_type, event_data in claude_service.stream_chat(message, jwt_token):
            yield f"event: {event_type}\ndata: {json.dumps(event_data, ensure_ascii=False)}\n\n"
        yield "event: done\ndata: {\"message\": \"complete\"}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')
```

### Alpine.js フロントエンド実装パターン

```javascript
// frontend/templates/ai_assistant.html
function sendMessage() {
    const es = new EventSource(`/api/v1/ai-assistant/stream?...`);
    // または POST + fetch でも可（後述）

    es.addEventListener('text_delta', (e) => {
        const data = JSON.parse(e.data);
        this.streamingText += data.text;  // リアルタイム追記
    });

    es.addEventListener('tool_start', (e) => {
        const data = JSON.parse(e.data);
        this.toolCalls.push({ name: data.tool_name, input: data.tool_input });
    });

    es.addEventListener('done', () => {
        es.close();
        this.isStreaming = false;
    });

    es.addEventListener('error', (e) => {
        es.close();
        this.showError(JSON.parse(e.data).error);
    });
}
```

> **注意**: `EventSource` は GET リクエストのみサポート。POST でメッセージを送る場合は `fetch` + `ReadableStream` を使うか、セッションにメッセージを一時保存する方式を検討する（Phase 4-4 で実装方針を確定する）。

---

## セキュリティ考慮事項

- Claude API Key は Fernet 対称暗号で暗号化して DB に保存する
- 暗号化キーは環境変数（`ENCRYPTION_KEY`）で管理する
- MCP 経由のクエリも既存の `accountId` テナント分離を維持する
- SSE エンドポイントも `@login_required` で保護する

---

## 影響範囲の分析

- 既存機能（Phase 1〜3）への影響: **なし**（新規追加のみ）
- DB マイグレーション: **あり**（`User` テーブルに `claude_api_key_encrypted` カラム追加）
- 新規 Python 依存: `anthropic`, `cryptography`
