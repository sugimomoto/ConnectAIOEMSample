# design.md

## 実装アプローチ

`externalId` の生成箇所は `backend/services/auth_service.py` の1行のみ。
変更は最小限にとどめ、影響範囲を抑える。

## 変更するファイル

### 1. `backend/services/auth_service.py`（本体修正）

| | コード |
|---|---|
| **変更前** | `child_account_id = client.create_account(str(user.id))` |
| **変更後** | `child_account_id = client.create_account(user.email)` |

`user.email` は DB への INSERT・`commit()` 完了後に確定しており、
`user.id` と同じタイミングで安全に参照できる。

### 2. `backend/tests/conftest.py`（テスト修正）

`mock_connect_ai` フィクスチャで `create_account` の呼び出し引数を検証している箇所があれば、
期待値を `user.email` に更新する。
現状はモックの戻り値のみ設定しており引数の assert はないため、変更不要の可能性が高い。

### 3. `backend/tests/test_auth.py`（テスト修正）

`test_register_saves_child_account_id` は戻り値（`connect_ai_account_id`）のみを検証しており、
`create_account` への引数は検証していない。変更不要。

引数を明示的に検証するテストケースを1件追加する。

```python
def test_register_uses_email_as_external_id(client, app, mock_connect_ai):
    """externalId としてメールアドレスが使用されること"""
    _register(client, email="user@example.com")
    mock_connect_ai.assert_called_once_with("user@example.com")
```

### 4. `docs/glossary.md`（ドキュメント修正）

`externalId` の定義を `users.id` から `users.email` に更新する。

| | 内容 |
|---|---|
| **変更前** | `external_id = str(user.id)  # 例: "42"` |
| **変更後** | `external_id = user.email  # 例: "alice@example.com"` |

## データ構造の変更

なし。`users` テーブルのスキーマ変更は不要。

## 影響範囲の分析

| ファイル | 変更種別 | 影響度 |
|---|---|---|
| `backend/services/auth_service.py` | 修正（1行） | 小 |
| `backend/tests/test_auth.py` | テスト追加（1件） | 小 |
| `docs/glossary.md` | ドキュメント修正 | 小 |
| `backend/connectai/client.py` | 変更なし | なし |
| `backend/tests/conftest.py` | 変更なし | なし |

## 非互換性

- 既存の CData 子アカウント（`externalId = str(user.id)` で作成済み）との後方互換性はない
- サンプルアプリのため既存データ移行は不要とする
