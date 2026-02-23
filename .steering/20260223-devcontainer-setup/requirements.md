# 要求定義: DevContainer 設定の追加

**作業ディレクトリ**: `.steering/20260223-devcontainer-setup/`
**作成日**: 2026-02-23

---

## 1. 背景・目的

チームメンバーが同一の開発環境でローカル開発できるよう、VS Code Dev Containers 対応の設定ファイルを追加する。
合わせて、RSA 秘密鍵をファイル配置なしで `.env` の環境変数から渡せるよう対応する。

---

## 2. 変更内容

### 新規作成

#### `.devcontainer/devcontainer.json`

- ベースイメージ: `mcr.microsoft.com/devcontainers/python:3.11`
- ポート転送: 5001
- postCreateCommand: `bash .devcontainer/setup.sh`
- 環境変数: `PYTHONPATH=/workspaces/<プロジェクト名>`
- VS Code 拡張機能: Python, Pylance, debugpy
- VS Code 設定: pytest パス等

#### `.devcontainer/setup.sh`

コンテナ初回作成時に自動実行されるセットアップスクリプト。

1. `pip install -r backend/requirements.txt`
2. `backend/.env` が未作成の場合は `backend/.env.example` からコピー
3. `backend/keys/` ディレクトリ作成
4. `flask --app backend.app db upgrade` で DB マイグレーション実行

### 変更

#### `backend/connectai/jwt.py`

RSA 秘密鍵の読み込みに `CONNECT_AI_PRIVATE_KEY` 環境変数を優先対応する。

- `CONNECT_AI_PRIVATE_KEY`（env var）が設定されていればその PEM 文字列を使用
- 未設定の場合は従来どおり `CONNECT_AI_PRIVATE_KEY_PATH` のファイルパスから読み込み
- 既存のファイルパス方式との後方互換性を維持

#### `backend/config.py`

- `CONNECT_AI_PRIVATE_KEY: str` 設定項目を追加（デフォルト: 空文字列）

#### `backend/.env.example`

- `CONNECT_AI_PRIVATE_KEY` のコメント付きサンプルを追記

---

## 3. 受け入れ条件

- VS Code で「Reopen in Container」を実行すると `setup.sh` が自動実行される
- コンテナ起動後、`backend/.env` に必要な環境変数を設定するだけでアプリが起動できる
- `CONNECT_AI_PRIVATE_KEY` に PEM 文字列を設定すれば `backend/keys/private.key` なしで JWT 生成できる
- 既存のファイルパス方式（`CONNECT_AI_PRIVATE_KEY_PATH`）は引き続き動作する
- `pytest backend/tests/ -v` が全 PASS すること

---

## 4. 制約事項

- `.devcontainer/` はプロジェクトルートに配置する
- `backend/keys/` や `backend/.env` はコンテナに含めない（git 管理外を維持）
- テストコードは変更しない
