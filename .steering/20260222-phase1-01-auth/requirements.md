# 要求内容: Phase 1-01 認証・アカウント管理

**作業ディレクトリ**: `.steering/20260222-phase1-01-auth/`
**作成日**: 2026-02-22
**対象フェーズ**: Phase 1 - 機能①

---

## 1. 作業概要

DataHubアプリケーションの認証基盤を実装する。
ユーザーのメール/パスワード登録・ログイン・ログアウトと、
ユーザー登録時のCData Connect AI 子アカウント自動作成を含む。

本作業が完了することで、後続の「コネクション管理」「メタデータエクスプローラー」の実装基盤が整う。

---

## 2. 機能要件

| 要求ID | 内容 | 優先度 |
|--------|------|--------|
| FR-AUTH-001 | メールアドレス・パスワード・名前でのユーザー登録 | P0 |
| FR-AUTH-002 | メールアドレス・パスワードでのログイン | P0 |
| FR-AUTH-002 | ログアウト（サーバー側セッション破棄） | P0 |
| FR-AUTH-003 | Flaskセッション（Cookie）によるセッション管理 | P0 |
| FR-AUTH-004 | テナント分離（自分のデータのみアクセス可能） | P0 |
| FR-AUTH-005 | ユーザー登録時にConnect AI Account APIで子アカウントを自動作成し、`ChildAccountId`を保存 | P0 |

---

## 3. ユーザーストーリー

### ストーリー A: 新規ユーザー登録
**As a** 新規ユーザー
**I want to** メールアドレス・パスワード・名前でアカウントを作成する
**So that** DataHubを利用できる状態になる

**受け入れ条件:**
- メール・パスワード・名前を入力して登録できる
- 登録済みのメールアドレスは使用できない（重複チェック）
- 登録完了後、自動的にログイン状態になりダッシュボードへ遷移する
- 登録時に内部でConnect AI子アカウントが作成される（ユーザーには見えない）

### ストーリー B: ログイン
**As a** 登録済みユーザー
**I want to** メールアドレスとパスワードでログインする
**So that** 自分のコネクションやデータにアクセスできる

**受け入れ条件:**
- 正しいメール・パスワードでログインするとダッシュボードへ遷移する
- 誤ったメール・パスワードではエラーメッセージが表示される
- ログイン状態はブラウザを閉じても保持される（JWTをlocalStorageに保存）

### ストーリー C: ログアウト
**As a** ログイン中のユーザー
**I want to** ログアウトする
**So that** 他の人が自分のアカウントにアクセスできないようにする

**受け入れ条件:**
- ログアウト後、ログイン画面へ遷移する
- ログアウト後、保護されたページにアクセスするとログイン画面へリダイレクトされる

### ストーリー D: 未認証アクセスのブロック
**As a** 未ログインのユーザー
**I want to** 保護されたページへのアクセスをブロックされる
**So that** 不正アクセスを防止できる

**受け入れ条件:**
- 未ログイン状態で `/api/v1/connections` 等のAPIを呼び出すと 401 が返る
- ブラウザで `/dashboard` 等の保護ページにアクセスすると `/login` にリダイレクトされる

---

## 4. 技術的な処理フロー

### セッション管理の方針

本アプリのブラウザ ↔ バックエンド間の認証は **Flask-Login（Cookie セッション）** で管理する。
デモ用途のためシンプルな実装を優先する。

| 種別 | 仕組み | 保存先 |
|------|--------|--------|
| **アプリセッション** | Flask-Login がログイン状態をサーバー側で管理。ブラウザには署名済みCookieを発行 | サーバー側（Flask session） |
| **Connect AI JWT**（RS256） | バックエンドがConnect AI APIを呼び出す**都度**生成 | 保存しない（使い捨て） |

- フロントエンド側でのトークン管理（localStorage 等）は不要
- ブラウザがCookieを自動付与するため、APIリクエスト時の認証ヘッダー操作が不要
- Connect AI JWTはバックエンド内で完結し、フロントエンドには渡さない

### ユーザー登録フロー

```
[ユーザー] → フォーム入力（メール・パスワード・名前）
    ↓
[フロントエンド] → POST /api/v1/auth/register
    ↓
[バックエンド]
  1. メールアドレスの重複チェック
  2. パスワードをbcryptでハッシュ化
  3. DBにUserレコード作成（connect_ai_account_id = NULL）
  4. Connect AI JWT（RS256）を生成（iss = ParentAccountId、sub = ""（空文字列））
     ※ 子アカウント未作成のため、初回は sub を空文字列にして呼び出す
  5. Connect AI Account APIを呼び出し
     POST /poweredby/account/create { "externalId": "user.id の文字列" }
  6. 返却された ChildAccountId を connect_ai_account_id に保存
  7. Flask-Login の login_user() でセッション開始
    ↓
[ブラウザ] → Cookieにセッション情報が付与される → /dashboard へリダイレクト
```

### ログインフロー

```
[ユーザー] → フォーム入力（メール・パスワード）
    ↓
[フロントエンド] → POST /api/v1/auth/login
    ↓
[バックエンド]
  1. メールアドレスでUserレコード検索
  2. bcryptでパスワード検証
  3. Flask-Login の login_user() でセッション開始
    ↓
[ブラウザ] → Cookieにセッション情報が付与される → /dashboard へリダイレクト
```

### ログアウトフロー

```
[ユーザー] → 「ログアウト」クリック
    ↓
[フロントエンド] → POST /api/v1/auth/logout
    ↓
[バックエンド] → Flask-Login の logout_user() でセッション破棄
    ↓
[ブラウザ] → /login へリダイレクト
```

---

## 5. 実装スコープ（対象ファイル）

本作業で新規作成・実装するファイル：

**バックエンド:**
- `backend/app.py` - Flaskアプリ初期化・Blueprint登録
- `backend/config.py` - 環境設定クラス
- `backend/models/__init__.py` - DB初期化
- `backend/models/user.py` - Userモデル
- `backend/schemas/user_schema.py` - 登録・ログインのPydanticスキーマ
- `backend/services/auth_service.py` - 認証ビジネスロジック
- `backend/connectai/jwt.py` - Connect AI用JWT生成（RS256）
- `backend/connectai/client.py` - Connect AI APIクライアント（Account API呼び出し）
- `backend/connectai/exceptions.py` - Connect AI固有の例外
- `backend/api/v1/__init__.py` - Blueprint定義
- `backend/api/v1/auth.py` - 認証エンドポイント
- `backend/middleware/error_handler.py` - グローバルエラーハンドラー
  ※ 保護エンドポイントには Flask-Login の `@login_required` デコレータを使用（別途middlewareファイル不要）
- `backend/migrations/` - Alembic初期マイグレーション（usersテーブル）
- `backend/requirements.txt`
- `backend/.env.example`

**フロントエンド:**
- `frontend/pages/login.html` - ログイン画面
- `frontend/pages/register.html` - ユーザー登録画面
- `frontend/pages/dashboard.html` - ダッシュボード（ログイン後のトップ画面）
- `frontend/static/js/api-client.js` - APIクライアント共通クラス
  ※ Cookie はブラウザが自動付与するため、認証ヘッダーの手動設定は不要
- `frontend/static/js/auth.js` - 認証処理（`logout`のフォーム送信等）

**プロジェクトルート:**
- `.env.example` - ルートの環境変数テンプレート
- `.gitignore`
- `README.md`（セットアップ手順）

---

## 6. 制約事項

- Connect AI Account APIの呼び出しが失敗した場合（ネットワークエラー等）でも、ユーザーレコードは作成済みのため、エラーメッセージを表示して再試行できるようにする
- `connect_ai_account_id` が NULL のユーザーは、コネクション作成等の機能を使えないように後続で制御する
- パスワードはbcrypt（cost factor: 10）でハッシュ化する
- Flaskセッションの署名には `SECRET_KEY` 環境変数を使用する（`.env` で管理、Gitにコミットしない）
- Connect AI JWT（RS256）のみ PyJWT + cryptography ライブラリを使用する

---

## 7. 完了の定義

- [ ] ユーザー登録APIが動作し、DBにレコードが作成される
- [ ] ユーザー登録時にConnect AI子アカウントが作成され、`ChildAccountId` が `connect_ai_account_id` カラムに保存される
- [ ] ログインAPIが動作し、Cookieセッションが発行される
- [ ] 未ログイン状態のAPIリクエストに401が返る
- [ ] フロントエンドの登録・ログイン画面が動作する
- [ ] ログアウト後にセッションが破棄され、ログイン画面へリダイレクトされる
- [ ] パスワードがDBに平文で保存されていない（bcryptハッシュ）
- [ ] 認証テスト（`tests/test_auth.py`）が通過する
