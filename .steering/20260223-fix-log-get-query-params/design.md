# 設計書: API Log への GET クエリパラメータ記録

**作業ディレクトリ**: `.steering/20260223-fix-log-get-query-params/`
**作成日**: 2026-02-23
**関連 Issue**: #6

---

## 1. 変更方針

`_get()` メソッド内で `_log()` を呼び出す前に、`params` の有無に応じて `log_path` を構築する。
`urllib.parse.urlencode` は Python 標準ライブラリのため追加依存なし。

---

## 2. 変更内容

### `backend/connectai/client.py` — `_get()` メソッド

```python
# 変更前
def _get(self, path: str, params: dict | None = None) -> dict:
    url = f"{self.base_url}{path}"
    start = time.monotonic()
    try:
        resp = requests.get(url, headers=self._headers(), params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        self._log(path, "GET", None, data, resp.status_code, start)
        return data
    except requests.HTTPError as e:
        self._log(path, "GET", None, {"error": e.response.text}, e.response.status_code, start)
        raise ConnectAIError(f"HTTP {e.response.status_code}: {e.response.text}") from e
    except requests.exceptions.JSONDecodeError as e:
        raise ConnectAIError(f"Invalid JSON (HTTP {resp.status_code}): {resp.text[:500]!r}") from e
    except requests.RequestException as e:
        raise ConnectAIError(f"Request failed: {e}") from e
```

```python
# 変更後
def _get(self, path: str, params: dict | None = None) -> dict:
    from urllib.parse import urlencode
    url = f"{self.base_url}{path}"
    log_path = f"{path}?{urlencode(params)}" if params else path
    start = time.monotonic()
    try:
        resp = requests.get(url, headers=self._headers(), params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        self._log(log_path, "GET", None, data, resp.status_code, start)
        return data
    except requests.HTTPError as e:
        self._log(log_path, "GET", None, {"error": e.response.text}, e.response.status_code, start)
        raise ConnectAIError(f"HTTP {e.response.status_code}: {e.response.text}") from e
    except requests.exceptions.JSONDecodeError as e:
        raise ConnectAIError(f"Invalid JSON (HTTP {resp.status_code}): {resp.text[:500]!r}") from e
    except requests.RequestException as e:
        raise ConnectAIError(f"Request failed: {e}") from e
```

### 変更点のまとめ

| 変更箇所 | 変更前 | 変更後 |
|---------|-------|-------|
| `from urllib.parse import urlencode` | なし | メソッド先頭に追加 |
| `log_path` 変数 | なし | `params` の有無で分岐して構築 |
| 成功時 `_log()` の第1引数 | `path` | `log_path` |
| エラー時 `_log()` の第1引数 | `path` | `log_path` |

---

## 3. 影響範囲

### 変更ファイル
- `backend/connectai/client.py` のみ（`_get()` メソッド内のみ）

### 影響なし
- `_post()` / `_delete()` — 変更しない
- `_log()` のシグネチャ — 変更しない
- `ApiLog` モデル / DB スキーマ — 変更しない
- フロントエンド — 変更しない
- テスト (`conftest.py`, `test_metadata.py` 等) — 既存テストへの影響なし

---

## 4. ログ出力例（変更後）

| 呼び出しメソッド | 記録される `endpoint` |
|---------------|---------------------|
| `get_catalogs()` | `/catalogs` |
| `get_schemas("Salesforce1")` | `/schemas?catalogName=Salesforce1` |
| `get_tables("Salesforce1", "dbo")` | `/tables?catalogName=Salesforce1&schemaName=dbo` |
| `get_columns("Salesforce1", "dbo", "Account")` | `/columns?catalogName=Salesforce1&schemaName=dbo&tableName=Account` |
| `get_datasources()` | `/poweredby/sources/list` |
| `get_connections()` | `/poweredby/connection/list` |
