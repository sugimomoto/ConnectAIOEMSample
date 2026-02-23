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

Claude に渡す MCP ツール定義（Anthropic SDK の `tools` パラメータ形式）:

```python
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
            "properties": {"catalogName": {"type": "string"}},
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
                "parameters": {"type": "object", "description": "@param 形式のパラメータ"}
            },
            "required": ["query"]
        }
    }
]
```

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
