# DataHub — CData Connect AI OEM サンプル

**CData Connect AI OEM** を SaaS 製品へ統合する方法を示すリファレンス実装です。エンドユーザーがデータソースのコネクションを管理し、メタデータの探索・ビジュアルクエリ・CRUD 操作を行える Web アプリケーションです。Connect AI が提供する統一 SQL インターフェースを通じて、多様なデータソースに対応します。

## 機能一覧

| 機能 | 説明 |
|---|---|
| **認証** | ユーザー登録・ログイン・セッション管理 |
| **コネクション管理** | Connect AI の OAuth フローを使ったデータソースコネクションの作成・削除 |
| **メタデータエクスプローラー** | カタログ → スキーマ → テーブル → カラムのドリルダウン閲覧 |
| **クエリビルダー** | カラム選択・WHERE 条件・ページネーション・CSV エクスポートを備えたビジュアル SELECT クエリ |
| **データブラウザー** | カラムメタデータから動的生成されたフォームによるレコードの一覧・作成・編集・削除 |
| **AI アシスタント** | 自然言語でデータを問い合わせる MCP チャット。SSE でトークンをリアルタイム表示し、ツール呼び出し履歴をアコーディオン UI で可視化 |

---

## 前提条件

- **CData Connect AI** の親アカウント（以下が必要です）
  - **親アカウント ID**
  - アカウントに登録済みの **RSA 秘密鍵**（PEM 形式）

---

## セットアップ

セットアップ方法は **DevContainer（推奨）** と **ローカル環境（手動）** の2種類があります。

---

### DevContainer / GitHub Codespaces（推奨）

Python や依存パッケージのセットアップが不要で、すぐに開発を始められます。

#### GitHub Codespaces で起動する

1. リポジトリページで **Code → Codespaces → Create codespace on main** をクリック
2. コンテナのビルドと自動セットアップが完了するまで待つ（初回は数分かかります）
3. `backend/.env` を編集して必要な値を設定する（後述）
4. **実行とデバッグ** パネルから **Flask: Run** を選択して **F5** を押す

#### ローカルの VS Code DevContainer で起動する

**前提条件：** Docker Desktop と VS Code の [Dev Containers 拡張機能](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) が必要です。

1. リポジトリをクローンする

```bash
git clone <リポジトリURL>
cd ConnectAIOEMSample
```

2. VS Code でフォルダを開き、通知バナーの **Reopen in Container** をクリック
   （またはコマンドパレット `Ctrl+Shift+P` → **Dev Containers: Reopen in Container**）
3. コンテナのビルドと自動セットアップが完了するまで待つ
4. `backend/.env` を編集して必要な値を設定する（後述）
5. **実行とデバッグ** パネルから **Flask: Run** を選択して **F5** を押す

#### DevContainer 環境での環境変数設定

コンテナ起動後、`backend/.env` に以下を設定します。

```dotenv
SECRET_KEY=ランダムな長い文字列に変更してください
CONNECT_AI_PARENT_ACCOUNT_ID=あなたの親アカウントID

# RSA 秘密鍵（ファイル配置が不要な環境変数方式を推奨）
# 改行を \n でエスケープして1行で記載してください
CONNECT_AI_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----\nMIIEow...\n-----END RSA PRIVATE KEY-----"

# Claude API Key 暗号化キー（AI アシスタント機能を使用する場合に必要）
# 以下のコマンドで生成してください
# python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
ENCRYPTION_KEY=生成した Fernet キーを貼り付けてください
```

> **Codespaces を使う場合の Tip:** リポジトリの **Settings → Secrets and variables → Codespaces** に `CONNECT_AI_PRIVATE_KEY` などを登録しておくと、`.env` を手動編集しなくても自動的に環境変数として利用できます。

---

### ローカル環境（手動セットアップ）

**前提条件：** Python 3.11 以上

#### 1. リポジトリをクローンする

```bash
git clone <リポジトリURL>
cd ConnectAIOEMSample
```

#### 2. Python 仮想環境を作成する

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows
```

#### 3. 依存パッケージをインストールする

```bash
pip install -r requirements.txt
```

#### 4. RSA 秘密鍵を配置する

`backend/keys/` ディレクトリを作成し、Connect AI の RSA 秘密鍵をコピーします。

```bash
mkdir -p backend/keys
cp /path/to/your/private.key backend/keys/private.key
```

#### 5. 環境変数を設定する

サンプルファイルをコピーして値を設定します。

```bash
cp backend/.env.example backend/.env
```

`backend/.env` を編集します。

```dotenv
# Flask
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=ランダムな長い文字列に変更してください

# データベース（デフォルトは SQLite。追加セットアップ不要）
DATABASE_URL=sqlite:///datahub.db

# CData Connect AI
CONNECT_AI_BASE_URL=https://cloud.cdata.com/api
CONNECT_AI_PARENT_ACCOUNT_ID=あなたの親アカウントID

# RSA 秘密鍵のファイルパス（プロジェクトルートからの相対パス）
CONNECT_AI_PRIVATE_KEY_PATH=backend/keys/private.key

# アプリのベース URL（OAuth コールバック URL の組み立てに使用）
APP_BASE_URL=http://localhost:5001

# Claude API Key 暗号化キー（AI アシスタント機能を使用する場合に必要）
# 以下のコマンドで生成してください
# python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
ENCRYPTION_KEY=生成した Fernet キーを貼り付けてください
```

#### 6. データベースを初期化する

```bash
cd ..  # プロジェクトルートに戻る
python3 -m flask --app backend.app:create_app db upgrade
```

#### 7. アプリを起動する

```bash
python3 -m flask --app backend.app:create_app run --port 5001
```

ブラウザで **http://localhost:5001** を開くと、ダッシュボードへ自動的にリダイレクトされます。

---

## 使い方

1. `/register` で新規アカウントを登録する
2. `/login` でログインする
3. **コネクション管理** から新しいコネクションを作成する
   - データソースの種類を選択する（例: Salesforce、QuickBooks、Azure DevOps）
   - Connect AI の OAuth 認証画面で認証を完了する
4. **コネクション管理** に戻り、作成済みのコネクション一覧を確認する
5. **メタデータエクスプローラー** でカタログ・スキーマ・テーブル・カラムを閲覧する
6. **クエリビルダー** でビジュアルフィルターを使って SELECT クエリを実行する
7. **データブラウザー** でレコードの閲覧・編集・削除を行う
8. **設定** 画面から自分の Claude API Key を登録する
9. **AI アシスタント** でカタログを選択して自然言語でデータを問い合わせる
   - カタログ未選択でも AI が自律的にデータソースを探索して回答する
   - 「新しい会話」ボタンで会話をリセットできる

---

## テストの実行

```bash
cd backend
pytest tests/
```

テストはインメモリ SQLite とモックを使用するため、外部サービスへの接続は不要です。

---

## VS Code でのデバッグ

`.vscode/launch.json` にデバッグ構成が含まれています。DevContainer / Codespaces・ローカル環境のどちらでも同じ手順で利用できます。

| 構成名 | 説明 |
|---|---|
| **Flask: Run** | Flask サーバーをデバッガー付きで起動（ポート 5001） |
| **pytest: All** | テストスイート全体を実行 |
| **pytest: Current File** | 現在開いているファイルのテストを実行 |

**実行とデバッグ** パネル（`Ctrl+Shift+D` / `Cmd+Shift+D`）から構成を選択し、**F5** を押して開始します。

> **Note:** デバッグ構成は VS Code で選択中の Python インタープリターを自動的に使用します。DevContainer 環境ではコンテナのシステム Python（`/usr/local/bin/python`）が、ローカル環境では `backend/venv` の Python が使われます。

---

## プロジェクト構造

```
ConnectAIOEMSample/
├── .devcontainer/       # DevContainer / GitHub Codespaces 設定
├── backend/
│   ├── api/v1/          # Flask ルートハンドラー（auth, connections, metadata, query, data,
│   │                    #   settings, ai_assistant）
│   ├── connectai/       # CData Connect AI API クライアント・JWT 生成
│   ├── models/          # SQLAlchemy モデル（User, ApiLog）
│   ├── schemas/         # Pydantic リクエストバリデーションスキーマ
│   ├── services/        # ビジネスロジック（ConnectionService, MetadataService,
│   │                    #   crypto_service, mcp_client, claude_service など）
│   ├── tests/           # pytest テストスイート（135 テスト）
│   ├── keys/            # RSA 秘密鍵（バージョン管理対象外）
│   ├── .env             # 環境変数（バージョン管理対象外）
│   ├── .env.example     # 環境変数のテンプレート
│   └── requirements.txt
├── frontend/
│   ├── pages/           # HTML ページ（Alpine.js + Tailwind CSS）
│   └── static/js/       # API クライアントおよびユーティリティ
├── docs/                # 永続的な設計ドキュメント
├── migrations/          # Flask-Migrate / Alembic マイグレーション
└── .vscode/             # VS Code デバッグ・設定ファイル
```

---

## 技術スタック

| レイヤー | 技術 |
|---|---|
| バックエンド | Python 3.11, Flask 3.0, Flask-Login, Flask-SQLAlchemy, Pydantic |
| データベース | SQLite（開発環境）/ SQLAlchemy 対応の任意の DB |
| フロントエンド | Alpine.js, Tailwind CSS（CDN 読み込み、ビルド不要） |
| 認証 | bcrypt パスワードハッシュ化、Connect AI API 向け RS256 JWT |
| AI アシスタント | Anthropic SDK (Claude API)、MCP Streamable HTTP クライアント、SSE ストリーミング |
| 暗号化 | cryptography (Fernet) — Claude API Key を DB に暗号化保存 (`ENCRYPTION_KEY`) |
| テスト | pytest, unittest.mock |

---

## 注意事項

- `backend/keys/` と `backend/.env` はバージョン管理対象外です。秘密鍵や認証情報を絶対にリポジトリにコミットしないでください。
- `APP_BASE_URL` は Connect AI アカウントに登録済みのコールバック URL と一致させてください。
- 本番環境では `FLASK_ENV=production` に設定し、`SECRET_KEY` に十分にランダムな値を使用し、本番用データベースに切り替えてください。
