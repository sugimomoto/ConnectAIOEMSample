# 要求内容: Phase 1-02 コネクション管理

**作業ディレクトリ**: `.steering/20260222-phase1-02-connections/`
**作成日**: 2026-02-22
**対象フェーズ**: Phase 1 - 機能②

---

## 1. 作業概要

ユーザーが外部データソース（Salesforce, QuickBooks 等）への接続を作成・管理する機能を実装する。
Connect AI の Connection API と連携し、認証情報の入力は Connect AI の画面に委譲する。

**コネクション情報はローカル DB に保存しない。**
一覧・削除はすべて Connect AI API を呼び出して操作する。
テナント分離は JWT の `sub` クレームに ChildAccountId を乗せることで Connect AI 側に委譲する。

本作業が完了することで、後続の「メタデータエクスプローラー」「クエリ実行」の基盤となるコネクションが利用可能になる。

---

## 2. 機能要件

| 要求ID | 内容 | 優先度 |
|--------|------|--------|
| FR-CONN-001 | コネクション名・データソース種別を指定して新規コネクションを作成できる | P0 |
| FR-CONN-002 | コネクション作成後、Connect AI の認証画面へリダイレクトされる | P0 |
| FR-CONN-003 | 認証完了後のコールバックでコネクション一覧画面へリダイレクトされる | P0 |
| FR-CONN-004 | 自分のコネクション一覧を表示できる | P0 |
| FR-CONN-005 | コネクションを削除できる | P0 |
| FR-CONN-006 | 他ユーザーのコネクションにはアクセスできない（Connect AI が ChildAccountId で保証） | P0 |
| FR-CONN-007 | コネクション作成画面でデータソース種別を Connect AI のデータソース一覧 API から取得し、セレクトボックスで選択できる | P0 |

---

## 3. ユーザーストーリー

### ストーリー A: コネクション作成
**As a** ログイン済みユーザー
**I want to** データソースへのコネクションを作成する
**So that** 自社データを DataHub で利用できる状態にする

**受け入れ条件:**
- フォームを開くと Connect AI のデータソース一覧 API から選択肢を取得し、セレクトボックスに表示される
- コネクション名とデータソース種別を選択して「作成」を実行できる
- 作成後、Connect AI の認証画面へリダイレクトされる
- Connect AI で認証情報を入力・完了すると `/callback` へ戻される
- コールバック画面からコネクション一覧画面（`/connections`）へ自動リダイレクトされる
- コネクション一覧に作成したコネクションが表示される

### ストーリー B: コネクション一覧表示
**As a** ログイン済みユーザー
**I want to** 自分のコネクション一覧を確認する
**So that** 接続可能なデータソースを把握できる

**受け入れ条件:**
- コネクション名・データソース種別・status が一覧に表示される
- 自分が作成したコネクションのみ表示される（Connect AI が ChildAccountId で保証）
- コネクションが存在しない場合は「コネクションがありません」のメッセージが表示される

### ストーリー C: コネクション削除
**As a** ログイン済みユーザー
**I want to** 不要なコネクションを削除する
**So that** 不要な接続情報を整理できる

**受け入れ条件:**
- 削除ボタンをクリックすると確認ダイアログが表示される
- 確認後、Connect AI 側のコネクションが削除され一覧から消える

---

## 4. 技術的な処理フロー

### データソース一覧取得フロー

```
[フロントエンド] → GET /api/v1/datasources
    ↓
[バックエンド]
  1. ログイン確認
  2. Connect AI JWT（RS256）を生成（sub = ChildAccountId）
  3. GET /poweredby/datasources を呼び出し
  4. 取得したデータソース一覧をレスポンスとして返す
    ↓
[フロントエンド] → セレクトボックスにデータソース名を表示
```

### コネクション作成フロー

```
[ユーザー] → 名前入力・データソースをセレクトボックスで選択して「作成」
    ↓
[フロントエンド] → POST /api/v1/connections
    ↓
[バックエンド]
  1. ログイン確認（@login_required）
  2. Connect AI JWT（RS256）を生成（sub = ChildAccountId）
  3. POST /poweredby/connection/create を呼び出し
     { "dataSource": "Salesforce", "name": "...",
       "redirectURL": "{APP_BASE_URL}/callback" }
  4. 返却された redirectURL をレスポンスに含める
  ※ ローカル DB への保存は行わない
    ↓
[フロントエンド] → Connect AI の認証画面へリダイレクト
    ↓
[ユーザー] → Connect AI で認証情報を入力・完了
    ↓
[ブラウザ] → /callback へリダイレクト
    ↓
[フロントエンド] → /connections へ自動リダイレクト
  ※ バックエンドへの activate 呼び出しは不要
```

### コネクション一覧取得フロー

```
[フロントエンド] → GET /api/v1/connections
    ↓
[バックエンド]
  1. ログイン確認
  2. Connect AI JWT（RS256）を生成（sub = ChildAccountId）
  3. GET /poweredby/connections を呼び出し
  4. Connect AI から返却されたコネクション一覧をそのままレスポンスとして返す
  ※ ローカル DB との突合は不要
    ↓
[フロントエンド] → コネクション一覧を表示
```

### コネクション削除フロー

```
[フロントエンド] → DELETE /api/v1/connections/{id}
    ↓
[バックエンド]
  1. ログイン確認
  2. Connect AI JWT（RS256）を生成（sub = ChildAccountId）
  3. DELETE /poweredby/connection/delete を呼び出し、Connect AI 側のコネクションを削除
  ※ ローカル DB の操作は不要
  ※ 他ユーザーのコネクション削除は Connect AI 側がエラーを返す
    ↓
[フロントエンド] → 一覧を再取得して表示更新
```

---

## 5. 実装スコープ（対象ファイル）

**バックエンド:**
- `backend/schemas/connection_schema.py` - Pydantic スキーマ
- `backend/services/connection_service.py` - コネクション操作ロジック
- `backend/connectai/client.py` - `get_datasources()` / `get_connections()` / `create_connection()` / `delete_connection()` メソッドを追加
- `backend/api/v1/connections.py` - コネクション API エンドポイント（データソース一覧含む）
- `backend/api/v1/__init__.py` - Blueprint に connections を追加
- `backend/tests/test_connections.py` - コネクションテスト

> `backend/models/connection.py` および `backend/migrations/` への connections テーブル追加は**不要**

**フロントエンド:**
- `frontend/pages/connections.html` - コネクション一覧画面
- `frontend/pages/connections-new.html` - コネクション作成フォーム画面
- `frontend/pages/callback.html` - コールバック受け取り画面（`/connections` へ自動リダイレクト）
- `frontend/static/js/api-client.js` - コネクション関連メソッドを追加

---

## 6. 制約事項

- コネクション情報（名前・データソース種別・status 等）はローカル DB に保存しない
- データソースの認証情報（パスワード・APIキー等）はアプリ側では保存しない（Connect AI が管理）
- `connect_ai_account_id` が NULL のユーザーはコネクション作成を禁止する（403 を返す）
- テナント分離は JWT の `sub = ChildAccountId` によって Connect AI 側で保証する
- コールバック URL は環境変数 `APP_BASE_URL` から組み立てる（ハードコードしない）

---

## 7. 完了の定義

- [ ] データソース一覧 API が Connect AI から取得した一覧を返す
- [ ] コネクション作成フォームのセレクトボックスにデータソース一覧が表示される
- [ ] コネクション作成 API が Connect AI に作成を依頼し、redirectURL を返す（ローカル DB 保存なし）
- [ ] Connect AI の認証画面へリダイレクトされる
- [ ] コールバック後に `/connections` へリダイレクトされる
- [ ] コネクション一覧 API が Connect AI から取得した一覧を返す
- [ ] コネクション削除 API が Connect AI 側のコネクションを削除する
- [ ] コネクションテスト（`tests/test_connections.py`）が通過する
- [ ] フロントエンドの一覧・作成・コールバック画面が動作する
