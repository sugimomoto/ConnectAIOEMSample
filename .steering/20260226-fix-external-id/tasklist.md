# tasklist.md

## タスク一覧

### 1. 本体修正
- [ ] `backend/services/auth_service.py` の `create_account(str(user.id))` を `create_account(user.email)` に変更

### 2. テスト追加
- [ ] `backend/tests/test_auth.py` に `test_register_uses_email_as_external_id` を追加

### 3. ドキュメント更新
- [ ] `docs/glossary.md` の `externalId` の定義を `user.email` に更新

### 4. 品質チェック
- [ ] `pytest backend/tests/` を実行してすべてのテストがパスすること

### 5. コミット & PR
- [ ] 変更をコミット
- [ ] `fix/external-id-use-email` ブランチを push
- [ ] Issue #16 を close する PR を作成

## 完了条件

- `pytest` が全テスト GREEN
- PR がレビュー可能な状態になっている
