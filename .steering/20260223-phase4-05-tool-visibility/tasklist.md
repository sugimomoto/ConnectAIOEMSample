# タスクリスト: Phase 4-5 - MCP ツール呼び出し可視化

**作成日**: 2026-02-23
**対応Issue**: [#11](https://github.com/sugimomoto/ConnectAIOEMSample/issues/11)
**ブランチ**: `feature/phase4-ai-assistant`
**要求・設計**: [20260223-ai-assistant/](../20260223-ai-assistant/)

## 成果物
AI が実行した MCP ツール呼び出しをアコーディオン UI で確認できる
（デモ時に「AI が Connect AI 経由でデータにアクセスしている」ことを視覚的に説明できる）

---

## タスク

### バックエンド: ツール呼び出し情報の収集
- [ ] `backend/services/claude_service.py` で agentic loop 中のツール呼び出しを記録
  - ツール名・入力引数・レスポンスサマリーを収集
  - SSE イベントとしてツール呼び出し情報を別途送信
    （例: `event: tool_call\ndata: {"name": "getTables", "input": {...}, "summary": "..."}\n\n`）

### フロントエンド: アコーディオン UI
- [ ] `frontend/templates/ai_assistant.html` を更新
  - 各 AI メッセージの下にツール呼び出し情報を表示
  - アコーディオン（折り畳み）形式で表示
    - ヘッダー: 「▶ ツール呼び出し（N件）」
    - 展開時: ツール名・引数・レスポンスサマリーのリスト
  - SSE の `tool_call` イベントを受信してリアルタイムに追加

## 完了条件
- [ ] AI 回答の下に「ツール呼び出し（N件）」が表示される
- [ ] クリックで展開し、ツール名・引数・結果サマリーが確認できる
- [ ] ツール呼び出しがない回答（挨拶など）ではアコーディオンが表示されない
