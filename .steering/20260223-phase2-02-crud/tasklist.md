# タスクリスト: Phase 2-02 データ CRUD 操作

**作業ディレクトリ**: `.steering/20260223-phase2-02-crud/`
**作成日**: 2026-02-23

---

## 進捗凡例

- `[ ]` 未着手
- `[x]` 完了

---

## フェーズ 1: 基盤スタブ作成

テストが import できる最低限の構造を用意する。

- [x] `backend/schemas/data_schema.py` を実装する（`RecordListSchema`, `RecordWriteSchema`, `RecordUpdateSchema`, `RecordDeleteSchema`）
- [x] `backend/services/data_service.py` を作成する（SQL 組み立て関数 + `DataService` メソッドはすべて `pass` のスタブ）
- [x] `backend/api/v1/data.py` を作成する（ページルートのみ実装、API エンドポイントは `NotImplementedError` のスタブ）
- [x] `backend/api/v1/__init__.py` に `from . import data` を追加する

---

## フェーズ 2: テスト実装（テストファースト）

実装前にテストケースを記述し、期待する振る舞いを確定する。

- [x] `backend/tests/conftest.py` に `mock_connect_ai_crud` fixture を追加する
  - `query_data.return_value = (["Id", "Name", "Industry"], [["001", "Acme Corp", "Technology"], ["002", "Widget Co", "Manufacturing"]])`
- [x] `backend/tests/test_data.py` を実装する（以下のケースを網羅）
  - API テスト
    - [x] `test_get_records_success` — 200 + columns / rows / total
    - [x] `test_get_records_requires_login` — 未認証で 401
    - [x] `test_get_records_missing_param` — 必須パラメータ欠如で 400
    - [x] `test_create_record_success` — 201 + message
    - [x] `test_create_record_requires_login` — 未認証で 401
    - [x] `test_update_record_success` — 200 + message
    - [x] `test_update_record_requires_login` — 未認証で 401
    - [x] `test_delete_record_success` — 200 + message
    - [x] `test_delete_record_requires_login` — 未認証で 401
  - SQL 組み立て単体テスト
    - [x] `test_build_select_sql` — `SELECT *` + `LIMIT 20 OFFSET 0`
    - [x] `test_build_count_sql` — `SELECT COUNT(*) AS [cnt]`
    - [x] `test_build_insert_sql` — `INSERT INTO ... VALUES (@s0, @s1)` + params 検証
    - [x] `test_build_update_sql` — `SET [col] = @s0 WHERE [col] = @w0` + params 検証
    - [x] `test_build_delete_sql` — `DELETE FROM ... WHERE [col] = @w0` + params 検証

---

## ⚠️ レビュー依頼（テスト実装後）

> **テストコードのレビューをお願いします。**
> テストケースの網羅性・mock fixture の構成を確認後、
> 次のフェーズ（バックエンド実装）へ進みます。

---

## フェーズ 3: バックエンド実装（テストを通す）

レビュー承認後、テストが PASS するよう実装を進める。

- [x] `backend/services/data_service.py` に SQL 組み立て関数を本実装する
  - [x] `build_select_sql(catalog, schema, table, limit, offset)` — `SELECT * FROM [...] LIMIT N OFFSET M`
  - [x] `build_count_sql(catalog, schema, table)` — `SELECT COUNT(*) AS [cnt] FROM [...]`
  - [x] `build_insert_sql(catalog, schema, table, data)` — パラメータ `@s0`, `@s1`, ...
  - [x] `build_update_sql(catalog, schema, table, data, where)` — SET `@s0...`, WHERE `@w0...`
  - [x] `build_delete_sql(catalog, schema, table, where)` — WHERE `@w0...`
- [x] `backend/services/data_service.py` の `DataService` クラスを本実装する
  - [x] `list_records()` — SELECT + COUNT（COUNT 失敗時は `total=-1` でグレースフル対応）
  - [x] `create_record()` — INSERT 実行
  - [x] `update_record()` — `where` が空の場合は `ValueError` を raise、UPDATE 実行
  - [x] `delete_record()` — `where` が空の場合は `ValueError` を raise、DELETE 実行
- [x] `backend/api/v1/data.py` を本実装する
  - [x] `GET /data-browser` — `data-browser.html` レンダリング
  - [x] `GET /api/v1/data/records` — `RecordListSchema` でバリデーション後 `list_records()`
  - [x] `POST /api/v1/data/records` — `RecordWriteSchema` でバリデーション後 `create_record()`
  - [x] `PUT /api/v1/data/records` — `RecordUpdateSchema` でバリデーション後 `update_record()`
  - [x] `DELETE /api/v1/data/records` — `RecordDeleteSchema` でバリデーション後 `delete_record()`
  - [x] `ValueError`（`where` 空）を 400 に、`ConnectAIError` を 502 にマッピングする
- [x] テストを実行して全ケースが通過することを確認する（`pytest backend/tests/`）

---

## フェーズ 4: フロントエンド実装

- [x] `frontend/static/js/api-client.js` に CRUD 関連メソッドを追加する
  - [x] `getRecords(connectionId, catalog, schemaName, table, limit, offset)`
  - [x] `createRecord(connectionId, catalog, schemaName, table, data)`
  - [x] `updateRecord(connectionId, catalog, schemaName, table, data, where)`
  - [x] `deleteRecord(connectionId, catalog, schemaName, table, where)`
- [x] `frontend/pages/data-browser.html` を実装する
  - [x] コネクション → カタログ → スキーマ → テーブルのカスケード選択
  - [x] キー列セレクター（WHERE 条件に使うカラムを指定）
  - [x] レコード一覧テーブル（カラムヘッダー + データ行 + 編集・削除ボタン）
  - [x] ページネーション（前へ / 次へ + 「N〜M 件目 / 全 X 件」ラベル）
  - [x] 「新規レコード追加」ボタン
  - [x] 作成・編集モーダル（カラムメタデータから動的フォーム生成）
  - [x] 削除確認インライン表示
  - [x] ローディング・エラー・成功メッセージ の各状態表示
- [x] `frontend/pages/dashboard.html` にデータブラウザへのリンクを追加する

---

## フェーズ 5: 動作確認

- [x] アプリを起動して `/data-browser` にアクセスし、画面が表示されることを確認する
- [x] コネクション → カタログ → スキーマ → テーブルを選択するとレコード一覧が表示されることを確認する
- [x] ページネーション（前へ / 次へ）が動作することを確認する
- [x] 「新規レコード追加」ボタンを押すとフォームが表示され、保存するとレコードが追加されることを確認する
- [x] 「編集」ボタンを押すと既存値がプリフィルされたフォームが表示され、保存すると更新されることを確認する
- [x] 「削除」ボタンを押すと確認が表示され、確認後にレコードが削除されることを確認する
- [x] 未ログイン状態で `/api/v1/data/records` にアクセスすると 401 が返ることを確認する
- [x] Connect AI エラー時（不正なテーブル名など）にエラーメッセージが UI 上に表示されることを確認する

---

## 完了の定義（DoD）チェックリスト

- [x] `GET /api/v1/data/records` がレコード一覧（columns / rows / total）を返す
- [x] `POST /api/v1/data/records` が INSERT を実行し成功メッセージを返す
- [x] `PUT /api/v1/data/records` が UPDATE を実行し成功メッセージを返す
- [x] `DELETE /api/v1/data/records` が DELETE を実行し成功メッセージを返す
- [x] `where` が空の場合は 400 が返る（全件更新・削除の防止）
- [x] CRUD テスト（`tests/test_data.py`）が全 14 ケース通過する
- [x] `pytest backend/tests/` で全テスト（既存 39 件 + 新規 14 件）が通過する
- [x] データブラウザ画面でカスケード選択・一覧・CRUD・ページネーションが動作する
- [x] フォームがカラムメタデータから動的に生成される
