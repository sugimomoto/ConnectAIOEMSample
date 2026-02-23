# タスクリスト: Phase 4-1 - 基盤整備

**作成日**: 2026-02-23
**対応Issue**: [#11](https://github.com/sugimomoto/ConnectAIOEMSample/issues/11)
**ブランチ**: `feature/phase4-01-infrastructure`
**要求・設計**: [20260223-ai-assistant/](../20260223-ai-assistant/)

## 成果物
ユーザーが Claude API Key を登録・保存・マスク表示できる

---

## タスク

### 環境セットアップ
- [x] `backend/requirements.txt` に `anthropic`, `cryptography` を追加
- [x] `backend/config.py` に `ENCRYPTION_KEY` 環境変数設定を追加
- [x] `backend/.env.example` に `ENCRYPTION_KEY` を追記

### データモデル拡張
- [x] `backend/models/user.py` の `User` モデルに `claude_api_key_encrypted` カラムを追加

### 暗号化ユーティリティ
- [x] `backend/services/crypto_service.py` を新規作成
  - Fernet 対称暗号による API Key 暗号化・復号関数

### 設定 API
- [x] `backend/api/v1/settings.py` を新規作成
  - `GET /settings` — 設定画面レンダリング
  - `POST /api/v1/settings/api-key` — API Key 保存（暗号化して DB に保存）
  - `DELETE /api/v1/settings/api-key` — API Key 削除
  - `GET /api/v1/settings/api-key/status` — API Key 保存済み確認
- [x] `backend/api/v1/__init__.py` に Blueprint 登録

### 設定画面 UI
- [x] `frontend/pages/settings.html` を新規作成
  - Claude API Key 入力フォーム
  - 保存済みの場合はマスク表示（`sk-ant-••••••••`）
  - 更新・削除ボタン

### ナビゲーション
- [x] `frontend/static/js/header.js` に「AI アシスタント」「設定」メニューを追加
- [x] `frontend/static/js/api-client.js` に設定関連メソッドを追加
  - `getApiKeyStatus()`, `saveApiKey()`, `deleteApiKey()`

### テスト
- [x] `backend/tests/conftest.py` に `ENCRYPTION_KEY` を追加
  - `StaticPool` 使用・アウター app context なし設計（Flask-Login セッション分離のため）
- [x] `backend/tests/test_settings.py` を新規作成（20 テスト）
  - `TestCryptoService`: 暗号化・復号ユニットテスト（4件）
  - `TestSettingsAuth`: 未認証アクセス制御（3件）
  - `TestApiKeyStatus`: API Key 状態確認（2件）
  - `TestSaveApiKey`: API Key 保存（6件）
  - `TestDeleteApiKey`: API Key 削除（3件）
  - `TestApiKeyIsolation`: ユーザー分離（2件）
- [x] 全 80 テスト通過確認（`python -m pytest backend/tests/ -v`）

## 完了条件
- [x] ユーザーが設定画面で Claude API Key を入力・保存できる
- [x] 保存後、マスク表示される
- [x] API Key が DB に暗号化して保存されていることを確認できる
- [x] API Key を削除できる
- [x] 全テスト通過（80/80）
