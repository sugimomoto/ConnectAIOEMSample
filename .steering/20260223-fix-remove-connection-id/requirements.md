# 要求定義: connectionId の削除とコネクション選択 UI の廃止

**作業ディレクトリ**: `.steering/20260223-fix-remove-connection-id/`
**作成日**: 2026-02-23
**関連 Issue**: #5

---

## 背景

Connect AI において `connectionId` と `catalogName` は同義であり、カタログ名そのものがコネクションを識別する。現在の実装は以下の 2 つの問題を抱えている。

1. メタデータ API（`/catalogs`, `/schemas`, `/tables`, `/columns`）に不要な `connectionId` パラメータを渡している
2. UI にコネクション選択ドロップダウンが存在するが、カタログ選択でコネクションが決まるため冗長

## 変更内容

### 1. メタデータ API から `connectionId` を削除

Connect AI メタデータ API の正しい仕様：

```
GET /catalogs
GET /schemas?catalogName=GoogleSheetConnection
GET /tables?catalogName=GoogleSheetConnection&schemaName=GoogleSheets
GET /columns?catalogName=GoogleSheetConnection&schemaName=GoogleSheets&tableName=CRM+Data
```

`connectionId` クエリパラメータは不要。接続先の特定は JWT（Bearer トークン）と `catalogName` によって行われる。

### 2. コネクション選択 UI の廃止

#### 現状のフロー
```
[コネクション選択 ▼] → [カタログ選択 ▼] → [スキーマ選択 ▼] → [テーブル選択 ▼]
```

#### 変更後のフロー
```
[カタログ選択 ▼] → [スキーマ選択 ▼] → [テーブル選択 ▼]
```

対象画面：
- メタデータエクスプローラー（`explorer.html`）
- クエリビルダー（`query.html`）
- データブラウザ（`data-browser.html`）

## 受け入れ条件

- メタデータ API 呼び出し時に `connectionId` がクエリパラメータに含まれない
- 各画面にコネクション選択ドロップダウンが存在しない
- カタログ選択が最初のステップとなり、画面初期表示時にカタログ一覧を取得する
- 既存の機能（スキーマ→テーブル→カラムのドリルダウン）が正常に動作する
- 既存のテストが通過する（必要に応じてテストを修正する）

## 制約事項

- コネクション一覧取得 API（`GET /connections`）は引き続き使用する（コネクション管理画面での削除機能のため）
- `connections.html` / `connections-new.html` / `callback.html` は変更対象外
