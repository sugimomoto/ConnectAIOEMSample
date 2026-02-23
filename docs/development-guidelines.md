# 開発ガイドライン: DataHub - Connect AI OEM リファレンス実装

**バージョン**: 1.0
**最終更新**: 2026-02-22

---

## 目次

1. [コーディング規約](#1-コーディング規約)
2. [Pythonコーディング規約](#2-pythonコーディング規約)
3. [JavaScriptコーディング規約](#3-javascriptコーディング規約)
4. [HTMLコーディング規約](#4-htmlコーディング規約)
5. [セキュリティガイドライン](#5-セキュリティガイドライン)
6. [テスト規約](#6-テスト規約)
7. [Git規約](#7-git規約)
8. [開発フロー](#8-開発フロー)

---

## 1. コーディング規約

### 1.1 基本原則

- **シンプルさ優先**: デモ用途のアプリケーションのため、過度な抽象化や設計パターンを避ける
- **可読性**: コードは書く人より読む人のために書く
- **一貫性**: プロジェクト内で同じスタイルを統一して使用する
- **セキュリティ**: 入力値の検証とパラメータ化クエリを徹底する

### 1.2 コメントの指針

コードを見れば分かることはコメントしない。**なぜそうしているか**（意図・背景）をコメントする。

```python
# 良い例: 意図を説明するコメント
# Connect AI側でユーザーのデータソース認証情報を管理するため、
# アプリ側ではstatusのみ保持する
connection = Connection(user_id=user_id, name=name, data_source=data_source, status="pending")

# 悪い例: コードの繰り返し
# connectionを作成する
connection = Connection(user_id=user_id, name=name, data_source=data_source, status="pending")
```

---

## 2. Pythonコーディング規約

### 2.1 スタイル

- **PEP 8**に準拠する
- インデント: **スペース4つ**
- 1行の最大文字数: **120文字**
- 文字列: **ダブルクォート** を優先

```python
# 良い例
message = "User not found"

# 悪い例
message = 'User not found'
```

### 2.2 型ヒント

すべての関数・メソッドに型ヒントを付与する。

```python
from typing import Optional, List

def get_user_connections(self, user_id: int) -> List[Connection]:
    ...

def find_user_by_email(self, email: str) -> Optional[User]:
    ...
```

### 2.3 クラス設計

#### Serviceクラス

- コンストラクタで依存する `db` セッションを受け取る（依存性注入）
- 1クラス1責務（認証・コネクション・メタデータ・クエリを混在させない）

```python
class AuthService:
    def __init__(self, db):
        self.db = db

    def register_user(self, email: str, password: str, name: str) -> User:
        ...
```

#### ConnectAIClientクラス

- `account_id` を受け取り、APIコールごとにJWTを生成する
- HTTP通信のエラーは `ConnectAIError` に変換して上位に伝搬させる

```python
class ConnectAIClient:
    def __init__(self, account_id: str):
        self.account_id = account_id
        self.base_url = os.getenv("CONNECT_AI_BASE_URL")
```

### 2.4 エラーハンドリング

- 予期されるエラーは明示的にキャッチし、意味のあるメッセージに変換する
- `except Exception` のような広いキャッチは使用しない（デバッグが困難になるため）
- Connect AI APIのエラーは `ConnectAIError` に変換し、HTTPエラーレスポンスに変換する

```python
# 良い例
try:
    response = self._request("POST", "/poweredby/account/create", json=payload)
except requests.HTTPError as e:
    raise ConnectAIError(f"Account creation failed: {e.response.status_code}") from e

# 悪い例
try:
    response = self._request("POST", "/poweredby/account/create", json=payload)
except Exception:
    pass  # エラーを握りつぶさない
```

### 2.5 Flaskエンドポイント

- エンドポイントの関数は薄く保つ（バリデーション→serviceへ委譲→レスポンス返却）
- Pydanticスキーマでリクエストをバリデーションする
- `@require_auth` デコレータで認証保護する

```python
@connections_bp.route("", methods=["POST"])
@require_auth
def create_connection(current_user: User):
    # 1. バリデーション
    schema = CreateConnectionSchema(**request.json)

    # 2. Serviceへ委譲
    connection, redirect_url = connection_service.create_connection(
        user_id=current_user.id,
        name=schema.name,
        data_source=schema.data_source,
    )

    # 3. レスポンス返却
    return jsonify({
        "connection": connection.to_dict(),
        "redirectURL": redirect_url,
    }), 201
```

### 2.6 データベース操作

- 直接SQLを書かず、SQLAlchemy ORM を使用する
- すべてのクエリに `user_id = current_user.id` のフィルタを付与してテナント分離を保つ

```python
# 良い例（テナント分離あり）
connections = db.session.query(Connection).filter_by(user_id=current_user.id).all()

# 悪い例（全ユーザーのデータが取得される）
connections = db.session.query(Connection).all()
```

---

## 3. JavaScriptコーディング規約

### 3.1 スタイル

- インデント: **スペース2つ**
- 文字列: **シングルクォート** を優先
- セミコロン: **あり**
- `var` は使用禁止。`const` を優先、再代入が必要な場合は `let` を使用

```javascript
// 良い例
const apiClient = new APIClient();
let currentPage = 1;

// 悪い例
var apiClient = new APIClient();
```

### 3.2 非同期処理

- `async/await` を使用する（`then/catch` チェーンより可読性が高いため）
- エラーハンドリングは `try/catch` を使用する

```javascript
// 良い例
async function loadConnections() {
    try {
        const data = await apiClient.getConnections();
        renderConnectionList(data.connections);
    } catch (error) {
        showError('コネクションの取得に失敗しました');
        console.error(error);
    }
}

// 悪い例
apiClient.getConnections()
    .then(data => renderConnectionList(data.connections))
    .catch(error => showError('失敗しました'));
```

### 3.3 DOM操作

- Alpine.jsのディレクティブ（`x-data`, `x-bind`, `x-on`等）を優先し、直接DOMを操作する `document.querySelector` を最小限に抑える
- Alpine.jsで表現できない複雑な操作のみ `static/js/` のJSファイルに記述する

```html
<!-- 良い例: Alpine.jsで状態管理 -->
<div x-data="{ isLoading: false, connections: [] }">
    <button @click="isLoading = true; await loadConnections()">
        更新
    </button>
    <template x-for="conn in connections" :key="conn.id">
        <div x-text="conn.name"></div>
    </template>
</div>
```

### 3.4 APIクライアントの使用

- バックエンドAPIとの通信はすべて `APIClient` クラス（`api-client.js`）を経由する
- ページのJSファイルから直接 `fetch()` を呼び出さない

```javascript
// 良い例
const apiClient = new APIClient();
const data = await apiClient.executeQuery(connectionId, query, parameters);

// 悪い例（直接fetchを呼び出す）
const response = await fetch('/api/v1/queries/execute', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: JSON.stringify({ connectionId, query })
});
```

---

## 4. HTMLコーディング規約

### 4.1 スタイリング

- スタイリングは **Tailwind CSSのユーティリティクラス** を使用する
- `custom.css` へのCSSの追記は Tailwind で表現できない場合のみに限定する
- インラインの `style=""` 属性は使用しない

```html
<!-- 良い例 -->
<button class="bg-blue-600 hover:bg-blue-700 text-white font-medium px-4 py-2 rounded-lg">
    接続する
</button>

<!-- 悪い例 -->
<button style="background-color: #2563EB; color: white; padding: 8px 16px;">
    接続する
</button>
```

### 4.2 共通レイアウト

- すべての保護ページ（認証必要ページ）は、ページ冒頭で `auth.js` の `requireAuth()` を呼び出す
- ナビゲーション（サイドバー・ヘッダー）は各HTMLに直接記述する（テンプレートエンジンの継承は使用しない）

```html
<!-- ページ先頭の認証チェック（全保護ページ共通） -->
<script>
    document.addEventListener('DOMContentLoaded', () => {
        requireAuth(); // 未認証の場合、/login にリダイレクト
    });
</script>
```

### 4.3 フォームバリデーション

- フォームのバリデーションはサーバーサイド（Pydantic）を正とする
- クライアントサイドはUX向上のための補助的なバリデーションに留める
- エラーメッセージはAPIレスポンスの `error.details` を表示する

---

## 5. セキュリティガイドライン

### 5.1 SQLインジェクション対策

Connect AI SQL APIに送るすべてのクエリは、必ずパラメータ化クエリを使用する。
ユーザー入力を文字列結合でSQLに埋め込む実装は**絶対に禁止**。

```python
# 必須: パラメータ化クエリ
query = "SELECT [Id], [Name] FROM [Account] WHERE [Industry] = @industry"
parameters = {
    "industry": {"dataType": 5, "value": user_input}
}

# 禁止: 文字列結合（SQLインジェクション脆弱性）
query = f"SELECT * FROM [Account] WHERE [Industry] = '{user_input}'"  # ❌
```

### 5.2 テナント分離

すべてのデータアクセスで `user_id` によるフィルタリングを徹底する。

```python
# 必須: user_idで絞り込む
connection = db.session.query(Connection).filter_by(
    id=connection_id,
    user_id=current_user.id  # 他ユーザーのデータへのアクセスを防ぐ
).first()

if not connection:
    return jsonify({"error": {"code": "NOT_FOUND"}}), 404
```

### 5.3 認証・認可

- すべての保護エンドポイントに `@require_auth` デコレータを付与する
- `@require_auth` を付与し忘れたエンドポイントを作らないよう、Blueprintのデフォルトで認証を要求する実装を検討する

### 5.4 秘密情報の管理

- `SECRET_KEY`（JWTシークレット）と `CONNECT_AI_PRIVATE_KEY`（RSA秘密鍵）は必ず環境変数から取得する
- コード内にハードコードしない
- `.env` ファイルはGitにコミットしない（`.gitignore` に記載）

```python
# 良い例
secret_key = os.getenv("SECRET_KEY")
if not secret_key:
    raise RuntimeError("SECRET_KEY environment variable is not set")

# 禁止: ハードコード
secret_key = "my-secret-key-12345"  # ❌
```

### 5.5 パスワード管理

- パスワードは必ず **bcrypt** でハッシュ化して保存する
- パスワードの平文をログに記録しない

```python
import bcrypt

# ハッシュ化
hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=10))

# 検証
is_valid = bcrypt.checkpw(password.encode("utf-8"), stored_hash)
```

---

## 6. テスト規約

本プロジェクトはデモ用途のため、テストは最小限の範囲とします。

### 6.0 テストファースト（TDD）の方針

**実装の前にテストを書く**ことを原則とします。

実装の順序：

1. **基盤スタブを用意する** — モデル・スキーマ・例外クラスなど、テストが `import` できる最低限の構造を作る（ロジックは書かない）
2. **テストを書く** — 期待する振る舞い（正常系・異常系）をテストコードとして記述する
3. **レビューを受ける** — テストケースの網羅性・モック方針を確認してから実装に進む
4. **実装する** — テストがパスするように実装を進める

この順序により、テストが仕様書として機能し、実装の意図が明確になります。

### 6.1 テスト対象

以下を優先的にテストします：

| 優先度 | 対象 | テストの種類 |
|--------|------|------------|
| 高 | 認証ロジック（登録・ログイン・JWTの検証） | ユニットテスト |
| 高 | テナント分離（他ユーザーのデータにアクセスできないこと） | インテグレーションテスト |
| 中 | コネクション作成・有効化フロー | インテグレーションテスト |
| 低 | メタデータ・クエリAPI（Connect AIのモック必要） | 任意 |

### 6.2 テストの書き方

- テストフレームワーク: **pytest**
- テスト用DBはインメモリSQLite（`sqlite:///:memory:`）を使用する
- Connect AI APIはモックを使用する（外部APIに依存しない）
- テスト関数名は `test_[対象]_[条件]_[期待結果]` の形式とする

```python
# conftest.py
import pytest
from backend.app import create_app

@pytest.fixture
def app():
    app = create_app({"TESTING": True, "DATABASE_URL": "sqlite:///:memory:"})
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()
```

```python
# test_auth.py
def test_register_success_creates_user(client):
    """正常なユーザー登録でユーザーが作成されること"""
    response = client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "password123",
        "name": "Test User"
    })
    assert response.status_code == 201
    assert "token" in response.json

def test_login_with_wrong_password_returns_401(client):
    """誤ったパスワードでログインすると401が返ること"""
    # ... 先にユーザー登録
    response = client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "wrong-password"
    })
    assert response.status_code == 401
```

### 6.3 テストの実行

```bash
# テストの実行
cd backend
pytest tests/ -v

# カバレッジレポートの生成（任意）
pytest tests/ --cov=. --cov-report=term-missing
```

---

## 7. Git規約

### 7.1 ブランチ戦略

デモ用プロジェクトのため、シンプルな構成とします。

```
main          # 安定版（動作確認済みのコード）
feature/*     # 機能追加
fix/*         # バグ修正
```

### 7.2 コミットメッセージ

**フォーマット:**
```
[種別] 変更内容の概要（50文字以内）

必要に応じて詳細な説明（72文字で折り返し）
- 変更の理由
- 影響範囲
```

**種別:**

| 種別 | 用途 |
|------|------|
| `feat` | 新機能の追加 |
| `fix` | バグ修正 |
| `docs` | ドキュメントのみの変更 |
| `refactor` | バグ修正・機能追加を伴わないコードの改善 |
| `test` | テストの追加・修正 |
| `chore` | ビルド設定・依存関係の更新 |

**例:**
```
feat: コネクション有効化APIを実装

- POST /api/v1/connections/:id/activate エンドポイントを追加
- Connect AI コールバック後に status を active に更新
- テナント分離のため user_id を検証
```

### 7.3 コミットの注意事項

- `.env` ファイルをコミットしない
- `private.key` 等の秘密鍵ファイルをコミットしない
- データベースファイル（`*.db`, `*.sqlite3`）をコミットしない
- 1コミットの変更は1つの論理的な変更にまとめる

---

## 8. 開発フロー

### 8.1 機能実装の手順

1. `.steering/[日付]-[機能名]/` のステアリングドキュメントを確認
2. `feature/[機能名]` ブランチを作成
3. `tasklist.md` の基盤フェーズを進める（モデル・スキーマ等のスタブ作成）
4. **テストを先に書く**（`conftest.py` と `test_*.py`）
5. **テストコードのレビューを受ける**（ケース網羅性・モック方針を確認）
6. レビュー承認後、テストがパスするよう実装を進める
7. 各タスク完了ごとにコミット
8. 実装完了後、リント・型チェックを実行
9. `main` にマージ

### 8.2 品質チェック

コードをコミットする前に以下を実行します。

```bash
# Pythonリント
cd backend
flake8 . --max-line-length=120 --exclude=migrations/

# Python型チェック（任意）
mypy . --ignore-missing-imports

# テスト実行
pytest tests/ -v
```

### 8.3 ローカル動作確認

```bash
# 仮想環境の有効化
source venv/bin/activate

# 依存パッケージのインストール
pip install -r backend/requirements.txt

# 環境変数の設定
cp .env.example .env
# .envを編集して各変数を設定

# DBマイグレーション
cd backend && flask db upgrade

# 開発サーバーの起動
flask run --debug
# → http://localhost:5000
```

---

**承認者**: _________________
**承認日**: _________________
