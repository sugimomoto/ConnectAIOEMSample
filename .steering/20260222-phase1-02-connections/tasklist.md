# タスクリスト: Phase 1-02 コネクション管理

**作業ディレクトリ**: `.steering/20260222-phase1-02-connections/`
**作成日**: 2026-02-23

---

## 進捗凡例

- `[ ]` 未着手
- `[x]` 完了

---

## フェーズ 1: 基盤スタブ作成

テストが import できる最低限の構造を用意する。

- [x] `backend/schemas/connection_schema.py` を実装する（`CreateConnectionSchema`）
- [x] `backend/services/connection_service.py` を作成する（メソッドは `pass` のスタブ）
- [x] `backend/api/v1/connections.py` を作成する（エンドポイントは `NotImplementedError` のスタブ）
- [x] `backend/api/v1/__init__.py` に `connections` Blueprint を追加する
- [x] `backend/.env.example` と `backend/config.py` に `APP_BASE_URL` を追加する

---

## フェーズ 2: テスト実装（テストファースト）

実装前にテストケースを記述し、期待する振る舞いを確定する。

- [x] `backend/tests/conftest.py` にコネクション関連 Connect AI モック fixture を追加する
- [x] `backend/tests/test_connections.py` を実装する（以下のケースを網羅）
  - [x] `test_get_datasources_success` — データソース一覧取得（200 + datasources）
  - [x] `test_get_datasources_requires_login` — 未認証（401）
  - [x] `test_get_connections_success` — コネクション一覧取得（200 + connections）
  - [x] `test_get_connections_requires_login` — 未認証（401）
  - [x] `test_create_connection_success` — 正常なコネクション作成（201 + redirectURL）
  - [x] `test_create_connection_without_child_account` — ChildAccountId 未設定（403）
  - [x] `test_create_connection_requires_login` — 未認証（401）
  - [x] `test_delete_connection_success` — 正常なコネクション削除（200）
  - [x] `test_delete_connection_requires_login` — 未認証（401）

---

## ⚠️ レビュー依頼（テスト実装後）

> **テストコードのレビューをお願いします。**
> テストケースの網羅性・モック fixture の構成を確認後、
> 次のフェーズ（バックエンド実装）へ進みます。

---

## フェーズ 3: バックエンド実装（テストを通す）

レビュー承認後、テストが PASS するよう実装を進める。

- [x] `backend/connectai/client.py` に `_get()` / `_delete()` メソッドを追加する
- [x] `backend/connectai/client.py` に `get_datasources()` を実装する
- [x] `backend/connectai/client.py` に `get_connections()` を実装する
- [x] `backend/connectai/client.py` に `create_connection()` を実装する
- [x] `backend/connectai/client.py` に `delete_connection()` を実装する
- [x] `backend/services/connection_service.py` を本実装に置き換える
- [x] `backend/api/v1/connections.py` を本実装に置き換える
- [x] テストを実行して全ケースが通過することを確認する（`pytest backend/tests/`）

---

## フェーズ 4: フロントエンド実装

- [x] `frontend/static/js/api-client.js` にコネクション関連メソッドを追加する（`getDatasources` / `getConnections` / `createConnection` / `deleteConnection`）
- [x] `frontend/pages/connections.html` を実装する（一覧表示・削除ボタン・「新規作成」リンク）
- [x] `frontend/pages/connections-new.html` を実装する（データソースセレクトボックス・作成フォーム・Connect AI へのリダイレクト）
- [x] `frontend/pages/callback.html` を実装する（完了メッセージ・`/connections` へ自動リダイレクト）
- [x] `frontend/pages/dashboard.html` にコネクション管理へのリンクを追加する

---

## フェーズ 5: 動作確認

- [x] アプリを起動して `/connections/new` のデータソースセレクトボックスに一覧が表示されることを確認する
- [x] コネクション作成フォームを送信し、Connect AI の認証画面へリダイレクトされることを確認する
- [x] 認証完了後に `/callback` → `/connections` へリダイレクトされることを確認する
- [x] `/connections` にコネクション一覧が表示されることを確認する
- [x] 削除ボタンで確認ダイアログが表示され、削除後に一覧から消えることを確認する
- [x] 未ログイン状態で `/api/v1/connections` にアクセスすると 401 が返ることを確認する

---

## 完了の定義（DoD）チェックリスト

- [x] データソース一覧 API が Connect AI から取得した一覧を返す
- [x] コネクション作成フォームのセレクトボックスにデータソース一覧が表示される
- [x] コネクション作成 API が Connect AI に作成を依頼し、redirectURL を返す（ローカル DB 保存なし）
- [x] Connect AI の認証画面へリダイレクトされる
- [x] コールバック後に `/connections` へリダイレクトされる
- [x] コネクション一覧 API が Connect AI から取得した一覧を返す
- [x] コネクション削除 API が Connect AI 側のコネクションを削除する
- [x] コネクションテスト（`tests/test_connections.py`）が通過する
- [x] フロントエンドの一覧・作成・コールバック画面が動作する
