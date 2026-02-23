# タスクリスト: Phase 3-01 Connect AI API リクエストログ

**作業ディレクトリ**: `.steering/20260223-phase3-01-api-log/`
**作成日**: 2026-02-23

---

## 進捗凡例

- `[ ]` 未着手
- `[x]` 完了

---

## フェーズ 1: 基盤スタブ作成

テストが import できる最低限の構造を用意する。

- [ ] `backend/models/api_log.py` を作成する（`ApiLog` モデル）
- [ ] `backend/models/__init__.py` に `from .api_log import ApiLog` を追加する
- [ ] `backend/services/api_log_service.py` を作成する（メソッドは `pass` のスタブ）
- [ ] `backend/api/v1/api_log.py` を作成する（ページルートのみ実装、API エンドポイントは `NotImplementedError` のスタブ）
- [ ] `backend/api/v1/__init__.py` に `from . import api_log` を追加する

---

## フェーズ 2: テスト実装（テストファースト）

実装前にテストケースを記述し、期待する振る舞いを確定する。

- [ ] `backend/tests/conftest.py` に `second_user` fixture を追加する（ユーザー分離テスト用）
- [ ] `backend/tests/test_api_log.py` を実装する（以下のケースを網羅）
  - API テスト
    - [ ] `test_get_api_logs_success` — 200 + logs / total
    - [ ] `test_get_api_logs_requires_login` — 未認証で 401
    - [ ] `test_clear_api_logs_success` — 200 + 自ユーザーのログのみ削除
    - [ ] `test_clear_api_logs_requires_login` — 未認証で 401
    - [ ] `test_other_user_logs_not_visible` — 他ユーザーのログが一覧に含まれない

---

## ⚠️ レビュー依頼（テスト実装後）

> **テストコードのレビューをお願いします。**
> テストケースの網羅性・mock fixture の構成を確認後、
> 次のフェーズ（バックエンド実装）へ進みます。

---

## フェーズ 3: バックエンド実装（テストを通す）

レビュー承認後、テストが PASS するよう実装を進める。

- [ ] `backend/models/api_log.py` の `ApiLog` モデルを本実装する
  - [ ] `user_id`（FK: `users.id`）、`timestamp`、`method`、`endpoint`、`request_body`、`response_body`、`status_code`、`elapsed_ms` カラム
- [ ] `flask db migrate -m "add api_logs table"` を実行してマイグレーションファイルを生成する
- [ ] `flask db upgrade` を実行してテーブルを作成する
- [ ] `backend/services/api_log_service.py` を本実装する
  - [ ] `list_logs(user_id, limit, offset)` — `user_id` で絞り込み、`timestamp` 降順
  - [ ] `clear_logs(user_id)` — `user_id` に一致するログのみ削除
- [ ] `backend/api/v1/api_log.py` を本実装する
  - [ ] `GET /api-log` — `api-log.html` レンダリング
  - [ ] `GET /api/v1/api-logs` — `list_logs()` を呼び出してログ一覧を返す
  - [ ] `DELETE /api/v1/api-logs` — `clear_logs()` を呼び出して自ユーザーのログを削除
- [ ] `backend/connectai/client.py` にログ記録処理を追加する
  - [ ] モジュールレベルに `_save_log_async(app, user_id, ...)` 関数を追加する
  - [ ] `_log(path, method, request_body, response_body, status_code, start)` インスタンスメソッドを追加する（未認証時はスキップ）
  - [ ] `_get()` にログ呼び出しを追加する（正常系・エラー系）
  - [ ] `_post()` にログ呼び出しを追加する（正常系・エラー系）
  - [ ] `_delete()` にログ呼び出しを追加する（正常系・エラー系）
- [ ] テストを実行して全ケースが通過することを確認する（`pytest backend/tests/`）

---

## フェーズ 4: フロントエンド実装

- [ ] `frontend/static/js/api-client.js` に API ログ関連メソッドを追加する
  - [ ] `getApiLogs(limit, offset)`
  - [ ] `clearApiLogs()`
- [ ] `frontend/pages/api-log.html` を実装する
  - [ ] ログ一覧テーブル（タイムスタンプ・メソッド・エンドポイント・ステータス・処理時間）
  - [ ] 行クリックで詳細モーダル（リクエスト/レスポンス JSON を左右 2 ペインで整形表示）
  - [ ] ページネーション（前へ / 次へ + 「N〜M 件目 / 全 X 件」ラベル）
  - [ ] 「ログをクリア」ボタン（確認ダイアログ付き）
  - [ ] ローディング・エラー・空状態の各状態表示
- [ ] `frontend/pages/dashboard.html` に API ログ画面へのリンクを追加する

---

## フェーズ 5: 動作確認

- [ ] アプリを起動して各画面を操作し、`/api-log` にログが記録されることを確認する
- [ ] メタデータエクスプローラーでのカタログ取得が GET ログとして記録されることを確認する
- [ ] クエリビルダーでのクエリ実行が POST ログとして記録されることを確認する
- [ ] コネクション削除が DELETE ログとして記録されることを確認する
- [ ] 別ユーザーでログインしても相手のログが見えないことを確認する
- [ ] 「ログをクリア」で自分のログのみ削除されることを確認する
- [ ] 未認証で `/api-log` にアクセスすると `/login` にリダイレクトされることを確認する

---

## 完了の定義（DoD）チェックリスト

- [ ] Connect AI への全 API 呼び出しがログインユーザーに紐付いて DB に保存される
- [ ] ログ保存の失敗がアプリの動作に影響しない（バックグラウンドスレッドで非同期処理）
- [ ] `GET /api/v1/api-logs` が自ユーザーのログ一覧（logs / total）を返す
- [ ] `DELETE /api/v1/api-logs` が自ユーザーのログのみを削除する
- [ ] 他ユーザーのログは一覧に表示されない
- [ ] API ログテスト（`tests/test_api_log.py`）が全 5 ケース通過する
- [ ] `pytest backend/tests/` で全テスト（既存含む）が通過する
- [ ] `/api-log` 画面でログ一覧・詳細モーダル・ページネーション・クリアが動作する
