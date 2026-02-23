# 要求定義: API Log への GET クエリパラメータ記録

**作業ディレクトリ**: `.steering/20260223-fix-log-get-query-params/`
**作成日**: 2026-02-23
**関連 Issue**: #6

---

## 1. 背景・問題

`backend/connectai/client.py` の `_get()` メソッドは、API 呼び出し結果を DB に記録する際に `_log()` へ `path` のみを渡している。そのため、GET リクエストのクエリパラメータ（例: `catalogName=Salesforce1&schemaName=dbo`）が API Log に保存されない。

一方、`_post()` はリクエストボディを `_log()` の `request_body` 引数として渡しているため、POST リクエストの内容は正しく記録されている。

**現在の動作（バグあり）:**
- `/schemas?catalogName=Salesforce1` を呼び出しても、ログには `/schemas` のみが記録される
- どのカタログ・スキーマ・テーブルのメタデータを取得したか追跡できない

**期待する動作:**
- `/schemas?catalogName=Salesforce1` を呼び出した場合、ログにも `/schemas?catalogName=Salesforce1` が記録される
- クエリパラメータを含む完全なエンドポイント情報が API Log に保存される

---

## 2. 変更内容

### 対象ファイル

- `backend/connectai/client.py` の `_get()` メソッドのみ

### 変更内容

`_get()` メソッド内で `_log()` を呼び出す際に、`params` が存在する場合はクエリ文字列を `path` に付加した `log_path` を使用する。

---

## 3. 受け入れ条件

- `_get()` が `params` 付きで呼び出された場合、API Log の `endpoint` カラムにクエリパラメータが含まれる
  - 例: `GET /schemas?catalogName=Salesforce1`
- `_get()` が `params` なしで呼び出された場合（例: `/catalogs`）、挙動は変わらない
- 既存テストがすべて PASS すること

---

## 4. 制約事項

- `_log()` のシグネチャは変更しない（`endpoint` 引数の文字列内容のみ変更）
- `_post()` / `_delete()` は変更しない
- ログ記録の非同期処理は変更しない
