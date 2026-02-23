# タスクリスト: Phase 2-01 クエリビルダー

**作業ディレクトリ**: `.steering/20260223-phase2-01-query-builder/`
**作成日**: 2026-02-23

---

## 進捗凡例

- `[ ]` 未着手
- `[x]` 完了

---

## フェーズ 1: 基盤スタブ作成

テストが import できる最低限の構造を用意する。

- [x] `backend/schemas/query_schema.py` を作成する（`QueryRequestSchema`, `ConditionSchema`）
- [x] `backend/services/query_service.py` を作成する（`QueryService`, `build_query_sql` はスタブ）
- [x] `backend/api/v1/query.py` を作成する（エンドポイントは `NotImplementedError` のスタブ、ページルートのみ実装）
- [x] `backend/api/v1/__init__.py` に `from . import query` を追加する
- [x] `backend/connectai/client.py` に `query_data()` スタブを追加する（`NotImplementedError`）

---

## フェーズ 2: テスト実装（テストファースト）

実装前にテストケースを記述し、期待する振る舞いを確定する。

- [x] `backend/tests/conftest.py` に `mock_connect_ai_query` fixture を追加する
  - `query_data.return_value = (["Id", "Name"], [["001", "John Doe"], ["002", "Jane"]])`
- [x] `backend/tests/test_query.py` を実装する（以下のケースを網羅）
  - API テスト
    - [x] `test_execute_query_success` — 200 + columns/rows/total/elapsed_ms
    - [x] `test_execute_query_requires_login` — 未認証で 401
    - [x] `test_execute_query_missing_param` — 必須パラメータ欠如で 400
    - [x] `test_execute_query_select_star` — `columns=[]` で `query_data` が `SELECT *` で呼ばれること
    - [x] `test_execute_query_with_conditions` — 条件あり時に `query_data` が適切な引数で呼ばれること
    - [x] `test_execute_query_connect_ai_error` — Connect AI エラー時に 502
  - SQL 組み立て単体テスト
    - [x] `test_build_sql_no_conditions` — WHERE なし + `LIMIT 1000`
    - [x] `test_build_sql_single_condition` — `=` 演算子 + パラメータ
    - [x] `test_build_sql_like` — `LIKE` 演算子
    - [x] `test_build_sql_in` — `IN` → カンマ分割して複数パラメータ
    - [x] `test_build_sql_between` — `BETWEEN` → `@p0_a` / `@p0_b`
    - [x] `test_build_sql_select_columns` — 指定カラムのみ `SELECT`

---

## ⚠️ レビュー依頼（テスト実装後）

> **テストコードのレビューをお願いします。**
> テストケースの網羅性・モック fixture の構成を確認後、
> 次のフェーズ（バックエンド実装）へ進みます。

---

## フェーズ 3: バックエンド実装（テストを通す）

レビュー承認後、テストが PASS するよう実装を進める。

- [x] Connect AI Query API の実際のリクエスト/レスポンス形式を curl で検証する
- [x] `backend/connectai/client.py` の `query_data()` を本実装に置き換える
- [x] `backend/services/query_service.py` の `build_query_sql()` を本実装する
  - SELECT * / カラム指定
  - WHERE 条件（9 演算子すべて）+ `AND` 結合
  - `LIMIT 1000`
- [x] `backend/services/query_service.py` の `execute_query()` を本実装する
- [x] `backend/api/v1/query.py` を本実装に置き換える（必須パラメータ欠如時は 400）
- [x] テストを実行して全ケースが通過することを確認する（`pytest backend/tests/`）

---

## フェーズ 4: フロントエンド実装

- [x] `frontend/static/js/api-client.js` に `executeQuery()` メソッドを追加する
- [x] `frontend/pages/query.html` を実装する
  - [x] コネクション〜テーブルのカスケードプルダウン
  - [x] カラム選択（全選択チェックボックス + 個別チェックボックス）
  - [x] WHERE 条件行の追加・削除（BETWEEN 時は値欄 2 つ表示）
  - [x] 実行ボタン + ローディング・エラー表示
  - [x] 結果テーブル（件数・実行時間表示）
  - [x] クライアントサイドページネーション（20 件/ページ）
  - [x] CSV ダウンロードボタン
- [x] `frontend/pages/dashboard.html` にクエリビルダーへのリンクを追加する

---

## フェーズ 5: 動作確認

- [x] アプリを起動して `/query` にアクセスし、画面が表示されることを確認する
- [x] コネクション〜テーブルをプルダウンで選択できることを確認する
- [x] カラム選択（全選択 / 個別）が動作することを確認する
- [x] WHERE 条件を追加・削除できることを確認する
- [x] 「実行」で結果テーブルが表示され、件数・実行時間が出ることを確認する
- [x] ページネーションが動作することを確認する
- [x] CSV ダウンロードでファイルが保存されることを確認する
- [x] 未ログイン状態で `POST /api/v1/query` にアクセスすると 401 が返ることを確認する

---

## 完了の定義（DoD）チェックリスト

- [x] `POST /api/v1/query` が Connect AI からクエリ結果を返す
- [x] 9 演算子すべてで WHERE 条件が正しく組み立てられる
- [x] クエリテスト（`tests/test_query.py`）が全 12 ケース通過する
- [x] クエリビルダー画面でカラム選択・条件指定・実行・ページネーションが動作する
- [x] CSV ダウンロードが動作する
- [x] `pytest backend/tests/` で全テスト（既存含む）が通過する
