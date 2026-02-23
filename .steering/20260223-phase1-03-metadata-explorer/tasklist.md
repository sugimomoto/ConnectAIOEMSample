# タスクリスト: Phase 1-03 メタデータエクスプローラー

**作業ディレクトリ**: `.steering/20260223-phase1-03-metadata-explorer/`
**作成日**: 2026-02-23

---

## 進捗凡例

- `[ ]` 未着手
- `[x]` 完了

---

## フェーズ 1: 基盤スタブ作成

テストが import できる最低限の構造を用意する。

- [x] `backend/services/metadata_service.py` を作成する（メソッドは `pass` のスタブ）
- [x] `backend/api/v1/metadata.py` を作成する（エンドポイントは `NotImplementedError` のスタブ、ページルートのみ実装）
- [x] `backend/api/v1/__init__.py` に `from . import metadata` を追加する

---

## フェーズ 2: テスト実装（テストファースト）

実装前にテストケースを記述し、期待する振る舞いを確定する。

- [x] `backend/tests/conftest.py` にメタデータ関連 Connect AI モック fixture（`mock_connect_ai_metadata`）を追加する
- [x] `backend/tests/test_metadata.py` を実装する（以下のケースを網羅）
  - [x] `test_get_catalogs_success` — カタログ一覧取得（200 + catalogs）
  - [x] `test_get_catalogs_requires_login` — 未認証（401）
  - [x] `test_get_schemas_success` — スキーマ一覧取得（200 + schemas）
  - [x] `test_get_schemas_requires_login` — 未認証（401）
  - [x] `test_get_tables_success` — テーブル一覧取得（200 + tables）
  - [x] `test_get_tables_requires_login` — 未認証（401）
  - [x] `test_get_columns_success` — カラム一覧取得（200 + columns）
  - [x] `test_get_columns_requires_login` — 未認証（401）
  - [x] `test_get_catalogs_missing_param` — `connection_id` 欠如で 400

---

## ⚠️ レビュー依頼（テスト実装後）

> **テストコードのレビューをお願いします。**
> テストケースの網羅性・モック fixture の構成を確認後、
> 次のフェーズ（バックエンド実装）へ進みます。

---

## フェーズ 3: バックエンド実装（テストを通す）

レビュー承認後、テストが PASS するよう実装を進める。

- [x] Connect AI Metadata API の実際のエンドポイント・パラメータ・レスポンスキーを curl で検証する
- [x] `backend/connectai/client.py` の `_get()` メソッドに `params` 引数を追加する
- [x] `backend/connectai/client.py` に `get_catalogs()` を実装する
- [x] `backend/connectai/client.py` に `get_schemas()` を実装する
- [x] `backend/connectai/client.py` に `get_tables()` を実装する
- [x] `backend/connectai/client.py` に `get_columns()` を実装する
- [x] `backend/services/metadata_service.py` を本実装に置き換える
- [x] `backend/api/v1/metadata.py` を本実装に置き換える（必須パラメータ欠如時は 400）
- [x] テストを実行して全ケースが通過することを確認する（`pytest backend/tests/`）

---

## フェーズ 4: フロントエンド実装

- [x] `frontend/static/js/api-client.js` にメタデータ関連メソッドを追加する（`getCatalogs` / `getSchemas` / `getTables` / `getColumns`）
- [x] `frontend/pages/explorer.html` を実装する
  - [x] コネクション選択セレクトボックス
  - [x] カタログ一覧表示（カード形式）
  - [x] スキーマ一覧表示（カード形式）
  - [x] テーブル一覧表示（カード形式 + リアルタイムフィルタ）
  - [x] カラム詳細表示（テーブル形式：カラム名・データ型・NULL可否）
  - [x] ブレッドクラムナビゲーション（クリックで上位に戻る）
  - [x] ローディング・エラー・コネクションなし の各状態表示
- [x] `frontend/pages/dashboard.html` にエクスプローラーへのリンクを追加する

---

## フェーズ 5: 動作確認

- [x] アプリを起動して `/explorer` にアクセスし、コネクション一覧が表示されることを確認する
- [x] コネクションを選択するとカタログ一覧が表示されることを確認する
- [x] カタログ → スキーマ → テーブル → カラムとドリルダウンできることを確認する
- [x] ブレッドクラムをクリックして上位階層に戻れることを確認する
- [x] テーブル一覧のフィルタ入力で絞り込みができることを確認する
- [x] 未ログイン状態で `/api/v1/metadata/catalogs` にアクセスすると 401 が返ることを確認する

---

## 完了の定義（DoD）チェックリスト

- [x] `GET /api/v1/metadata/catalogs?connection_id=...` が Connect AI からカタログ一覧を返す
- [x] `GET /api/v1/metadata/schemas` / `tables` / `columns` が同様に動作する
- [x] メタデータテスト（`tests/test_metadata.py`）が全ケース通過する
- [x] エクスプローラー画面でドリルダウン・ブレッドクラムが動作する
- [x] テーブル一覧のフィルタリングが動作する
- [x] カラム詳細（カラム名・データ型・NULL可否）が表示される
- [x] `pytest backend/tests/` で全テスト（既存含む）が通過する
