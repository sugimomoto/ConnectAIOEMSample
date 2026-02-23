# タスクリスト: Phase 4-5 - MCP ツール呼び出し可視化

**作成日**: 2026-02-23
**対応Issue**: [#11](https://github.com/sugimomoto/ConnectAIOEMSample/issues/11)
**ブランチ**: `feature/phase4-05-tool-visibility`
**要求・設計**: [20260223-ai-assistant/](../20260223-ai-assistant/)

## 成果物
AI が実行した MCP ツール呼び出しをアコーディオン UI で確認できる
（デモ時に「AI が Connect AI 経由でデータにアクセスしている」ことを視覚的に説明できる）

---

## タスク

### バックエンド: ツール呼び出し情報の収集
- [x] `backend/services/claude_service.py` で SSE イベントとしてツール情報を送信
  - `tool_start`: ツール名・入力引数（Phase 4-4 で実装済み）
  - `tool_result`: ツール名・レスポンス内容（Phase 4-4 で実装済み）

### フロントエンド: アコーディオン UI
- [x] `frontend/pages/ai_assistant.html` を更新
  - `tool_start` イベント: `{ name, input, result: null }` で tool_calls に追加
  - `tool_result` イベント: 対応する tool_calls エントリに `result` を設定
  - アコーディオン展開時にレスポンスサマリー（最大200文字）を表示
  - ツール呼び出しがない回答ではアコーディオンが非表示

## 完了条件
- [x] AI 回答の下に「ツール呼び出し（N件）」が表示される
- [x] クリックで展開し、ツール名・引数・結果サマリーが確認できる
- [x] ツール呼び出しがない回答（挨拶など）ではアコーディオンが表示されない

### テスト
- [x] `backend/tests/test_ai_assistant_api.py` にツール可視化テストを追加
  - ツール呼び出しあり → `tool_start` / `tool_result` イベントが含まれる
  - ツール呼び出しなし → `tool_start` / `tool_result` イベントが含まれない
- [x] 全テスト通過確認（`python -m pytest backend/tests/ -v`）→ 134 passed
