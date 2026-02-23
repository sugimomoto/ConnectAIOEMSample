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

---

## 前提条件

- **Python 3.11 以上**
- **CData Connect AI** の親アカウント（以下が必要です）
  - **親アカウント ID**
  - アカウントに登録済みの **RSA 秘密鍵**（PEM 形式）

---

## セットアップ

### 1. リポジトリをクローンする

```bash
git clone <リポジトリURL>
cd ConnectAIOEMSample
```

### 2. Python 仮想環境を作成する

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows
```

### 3. 依存パッケージをインストールする

```bash
pip install -r requirements.txt
```

### 4. RSA 秘密鍵を配置する

`backend/keys/` ディレクトリを作成し、Connect AI の RSA 秘密鍵をコピーします。

```bash
mkdir -p backend/keys
cp /path/to/your/private.key backend/keys/private.key
```

### 5. 環境変数を設定する

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
```

### 6. データベースを初期化する

```bash
cd backend
flask db upgrade
```

### 7. アプリを起動する

```bash
flask run --port 5001
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

---

## テストの実行

```bash
cd backend
pytest tests/
```

テストはインメモリ SQLite とモックを使用するため、外部サービスへの接続は不要です。

---

## VS Code でのデバッグ

`.vscode/launch.json` にデバッグ構成が含まれています。

| 構成名 | 説明 |
|---|---|
| **Flask Run (Debug)** | Flask サーバーをデバッガー付きで起動（ポート 5001） |
| **pytest: All Tests** | テストスイート全体を実行 |
| **pytest: Current File** | 現在開いているファイルのテストを実行 |

**実行とデバッグ** パネル（`Cmd+Shift+D`）から構成を選択し、**F5** を押して開始します。

---

## プロジェクト構造

```
ConnectAIOEMSample/
├── backend/
│   ├── api/v1/          # Flask ルートハンドラー（auth, connections, metadata, query, data）
│   ├── connectai/       # CData Connect AI API クライアント
│   ├── models/          # SQLAlchemy モデル（User）
│   ├── schemas/         # Pydantic リクエストバリデーションスキーマ
│   ├── services/        # ビジネスロジック（ConnectionService, MetadataService など）
│   ├── tests/           # pytest テストスイート
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
| テスト | pytest, unittest.mock |

---

## 注意事項

- `backend/keys/` と `backend/.env` はバージョン管理対象外です。秘密鍵や認証情報を絶対にリポジトリにコミットしないでください。
- `APP_BASE_URL` は Connect AI アカウントに登録済みのコールバック URL と一致させてください。
- 本番環境では `FLASK_ENV=production` に設定し、`SECRET_KEY` に十分にランダムな値を使用し、本番用データベースに切り替えてください。
