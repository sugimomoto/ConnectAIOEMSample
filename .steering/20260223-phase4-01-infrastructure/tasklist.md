# タスクリスト: Phase 4-1 - 基盤整備

**作成日**: 2026-02-23
**対応Issue**: [#11](https://github.com/sugimomoto/ConnectAIOEMSample/issues/11)
**ブランチ**: `feature/phase4-ai-assistant`
**要求・設計**: [20260223-ai-assistant/](../20260223-ai-assistant/)

## 成果物
ユーザーが Claude API Key を登録・保存・マスク表示できる

---

## タスク

### 環境セットアップ
- [ ] `backend/requirements.txt` に `anthropic`, `cryptography` を追加
- [ ] `backend/config.py` に `ENCRYPTION_KEY` 環境変数設定を追加
- [ ] `backend/.env.example` に `ENCRYPTION_KEY` を追記

### データモデル拡張
- [ ] `backend/models.py` の `User` モデルに `claude_api_key_encrypted` カラムを追加
- [ ] DB マイグレーション（`db.create_all()` で対応）

### 暗号化ユーティリティ
- [ ] `backend/services/crypto_service.py` を新規作成
  - Fernet 対称暗号による API Key 暗号化・復号関数

### 設定 API
- [ ] `backend/routes/settings.py` を新規作成
  - `GET /settings` — 設定画面レンダリング
  - `POST /settings/api-key` — API Key 保存（暗号化して DB に保存）
  - `DELETE /settings/api-key` — API Key 削除
- [ ] `backend/app.py` に Blueprint 登録

### 設定画面 UI
- [ ] `frontend/templates/settings.html` を新規作成
  - Claude API Key 入力フォーム
  - 保存済みの場合はマスク表示（`sk-ant-••••••••`）
  - 更新・削除ボタン

### ナビゲーション
- [ ] `frontend/templates/base.html` に「設定」メニューを追加

## 完了条件
- [ ] ユーザーが設定画面で Claude API Key を入力・保存できる
- [ ] 保存後、マスク表示される
- [ ] API Key が DB に暗号化して保存されていることを確認できる
- [ ] API Key を削除できる
