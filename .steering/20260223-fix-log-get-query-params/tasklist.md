# タスクリスト: API Log への GET クエリパラメータ記録

**作業ディレクトリ**: `.steering/20260223-fix-log-get-query-params/`
**作成日**: 2026-02-23
**関連 Issue**: #6

---

## タスク一覧

### バックエンド

- [ ] **T-01** `backend/connectai/client.py` — `_get()` メソッドを修正
  - `from urllib.parse import urlencode` をメソッド先頭に追加
  - `log_path = f"{path}?{urlencode(params)}" if params else path` を追加
  - `_log(path, ...)` → `_log(log_path, ...)` に変更（成功時・HTTPError 時の2箇所）

### 動作確認

- [ ] **T-02** テスト実行・パス確認
  - `PYTHONPATH=$(pwd) pytest backend/tests/ -v` がすべて PASS すること

---

## 完了条件

- すべてのタスクが完了している
- `pytest backend/tests/` が全件 PASS
- API Log の `endpoint` カラムにクエリパラメータが含まれる（例: `/schemas?catalogName=Salesforce1`）
