# タスクリスト: Phase 1-01 認証・アカウント管理

**作業ディレクトリ**: `.steering/20260222-phase1-01-auth/`
**作成日**: 2026-02-22

---

## 進捗凡例

- `[ ]` 未着手
- `[x]` 完了

---

## フェーズ 1: 環境・プロジェクト基盤

テストを実行できる最小限の環境を整える。

- [x] `backend/requirements.txt` を作成する
- [x] `backend/.env.example` を作成する
- [x] `.env.example`（ルート）を作成する
- [x] `backend/` 配下のディレクトリ構造を作成する（`models/`, `schemas/`, `services/`, `connectai/`, `api/v1/`, `middleware/`, `tests/`）
- [x] `backend/config.py` を実装する（環境変数読み込み・設定クラス）
- [x] `backend/models/__init__.py` を実装する（`db = SQLAlchemy()` 生成）
- [x] `backend/models/user.py` を実装する（`User` モデル・`UserMixin` 継承）
- [x] `backend/connectai/__init__.py` を作成する（空ファイル）
- [x] `backend/connectai/exceptions.py` を実装する（`ConnectAIError`）
- [x] `backend/schemas/__init__.py` を作成する（空ファイル）
- [x] `backend/schemas/user_schema.py` を実装する（`RegisterSchema` / `LoginSchema`）
- [x] `backend/services/__init__.py` を作成する（空ファイル）
- [x] `backend/api/__init__.py` を作成する（空ファイル）
- [x] `backend/api/v1/__init__.py` を実装する（Blueprint 定義・登録）
- [x] `backend/middleware/__init__.py` を作成する（空ファイル）

---

## フェーズ 2: テスト実装（テストファースト）

実装前にテストケースを記述し、期待する振る舞いを確定する。

- [x] `backend/tests/__init__.py` を作成する（空ファイル）
- [x] `backend/tests/conftest.py` を実装する（in-memory SQLite・テスト用Flaskアプリ・Connect AI APIモック）
- [x] `backend/tests/test_auth.py` を実装する（以下のケースを網羅）
  - [x] 正常なユーザー登録（201 + DBレコード確認）
  - [x] 重複メールでの登録エラー（409）
  - [x] 正常なログイン（200 + Cookie発行確認）
  - [x] パスワード不一致でのログインエラー（401）
  - [x] 未認証での保護APIアクセス（401）
  - [x] ログアウト後のセッション破棄確認
  - [x] パスワードがDBにbcryptハッシュで保存されていることの確認

---

## ⚠️ レビュー依頼（テスト実装後）

> **テストコードのレビューをお願いします。**
> テストケースの網羅性・モックの方針・conftest の構成について確認後、
> 次のフェーズ（バックエンド実装）へ進みます。

---

## フェーズ 3: バックエンド実装（テストを通す）

レビュー承認後、テストがパスするよう実装を進める。

- [x] `backend/connectai/jwt.py` を実装する（RS256 JWT 生成）
- [x] `backend/connectai/client.py` を実装する（`ConnectAIClient.create_account()`）
- [x] `backend/services/auth_service.py` を実装する（`register()` / `login()` / `logout()`）
- [x] `backend/api/v1/auth.py` を実装する（ページルート・`/auth/register`, `/auth/login`, `/auth/logout`, `/auth/me`）
- [x] `backend/middleware/error_handler.py` を実装する（グローバルエラーハンドラー）
- [x] `backend/app.py` を実装する（Flask初期化・Flask-Login設定・Blueprint登録・unauthorized_handler）
- [x] テストを実行して全ケースが通過することを確認する（`pytest backend/tests/`）

---

## フェーズ 4: データベースマイグレーション

- [x] Alembic を初期化する（`flask db init`）
- [x] 初回マイグレーションを生成する（`flask db migrate -m "create users table"`）
- [x] マイグレーションを適用する（`flask db upgrade`）
- [x] `users` テーブルのスキーマをDBで確認する

---

## フェーズ 5: フロントエンド実装

- [x] `frontend/pages/` ディレクトリを作成する
- [x] `frontend/static/js/` ディレクトリを作成する
- [x] `frontend/static/js/api-client.js` を実装する（`APIClient` クラス・`credentials: 'include'`）
- [x] `frontend/static/js/auth.js` を実装する（ログアウト処理等）
- [x] `frontend/pages/login.html` を実装する（Alpine.js フォーム・エラーメッセージ表示）
- [x] `frontend/pages/register.html` を実装する（Alpine.js フォーム・エラーメッセージ表示）
- [x] `frontend/pages/dashboard.html` を実装する（ログイン状態確認・ログアウトボタン）

---

## フェーズ 6: 動作確認

- [x] アプリを起動して `/register` ページが表示されることを確認する
- [x] ユーザー登録フォームでアカウントを作成し、DBレコードを確認する
- [x] Connect AI Account API が呼び出され `connect_ai_account_id` が保存されることを確認する
- [x] ログインフォームで正常にログインし `/dashboard` へ遷移することを確認する
- [x] 未ログイン状態で `/dashboard` にアクセスすると `/login` へリダイレクトされることを確認する
- [x] 未ログイン状態で `/api/v1/auth/me` にアクセスすると 401 が返ることを確認する
- [x] ログアウト後にセッションが破棄され `/login` へ遷移することを確認する

---

## 完了の定義（DoD）チェックリスト

完了には以下をすべて満たすこと：

- [x] ユーザー登録APIが動作し、DBにレコードが作成される
- [x] ユーザー登録時にConnect AI子アカウントが作成され、`ChildAccountId` が `connect_ai_account_id` カラムに保存される
- [x] ログインAPIが動作し、Cookieセッションが発行される
- [x] 未ログイン状態のAPIリクエストに401が返る
- [x] フロントエンドの登録・ログイン画面が動作する
- [x] ログアウト後にセッションが破棄され、ログイン画面へリダイレクトされる
- [x] パスワードがDBに平文で保存されていない（bcryptハッシュ）
- [x] 認証テスト（`tests/test_auth.py`）が通過する
