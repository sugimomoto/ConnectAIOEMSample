"""
メタデータ API のテスト（テストファースト）

各テストは実装前に記述しているため、実装完了前は FAIL する。
"""
import pytest


# ---------------------------------------------------------------------------
# ヘルパー
# ---------------------------------------------------------------------------

def _register_and_login(client, email="user@example.com", password="password123", name="Test User"):
    """ユーザーを登録してログインし、セッションを確立する"""
    client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "name": name,
    })
    client.post("/api/v1/auth/login", json={
        "email": email,
        "password": password,
    })


# ---------------------------------------------------------------------------
# カタログ一覧取得
# ---------------------------------------------------------------------------

def test_get_catalogs_success(client, mock_connect_ai_metadata):
    """ログイン済みユーザーがカタログ一覧を取得できること"""
    _register_and_login(client)
    resp = client.get("/api/v1/metadata/catalogs?connection_id=conn-001")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "catalogs" in data
    assert len(data["catalogs"]) == 1
    assert data["catalogs"][0]["TABLE_CATALOG"] == "Salesforce1"
    mock_connect_ai_metadata["catalogs"].assert_called_once_with("conn-001")


def test_get_catalogs_requires_login(client, mock_connect_ai_metadata):
    """未認証でのカタログ一覧取得は 401 が返ること"""
    resp = client.get("/api/v1/metadata/catalogs?connection_id=conn-001")
    assert resp.status_code == 401


def test_get_catalogs_missing_param(client, mock_connect_ai_metadata):
    """`connection_id` 未指定で 400 が返ること"""
    _register_and_login(client)
    resp = client.get("/api/v1/metadata/catalogs")
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# スキーマ一覧取得
# ---------------------------------------------------------------------------

def test_get_schemas_success(client, mock_connect_ai_metadata):
    """ログイン済みユーザーがスキーマ一覧を取得できること"""
    _register_and_login(client)
    resp = client.get("/api/v1/metadata/schemas?connection_id=conn-001&catalog_name=Salesforce1")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "schemas" in data
    assert len(data["schemas"]) == 1
    assert data["schemas"][0]["TABLE_SCHEMA"] == "dbo"
    mock_connect_ai_metadata["schemas"].assert_called_once_with("conn-001", "Salesforce1")


def test_get_schemas_requires_login(client, mock_connect_ai_metadata):
    """未認証でのスキーマ一覧取得は 401 が返ること"""
    resp = client.get("/api/v1/metadata/schemas?connection_id=conn-001&catalog_name=Salesforce1")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# テーブル一覧取得
# ---------------------------------------------------------------------------

def test_get_tables_success(client, mock_connect_ai_metadata):
    """ログイン済みユーザーがテーブル一覧を取得できること"""
    _register_and_login(client)
    resp = client.get(
        "/api/v1/metadata/tables?connection_id=conn-001&catalog_name=Salesforce1&schema_name=dbo"
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert "tables" in data
    assert len(data["tables"]) == 2
    assert data["tables"][0]["TABLE_NAME"] == "Account"
    assert data["tables"][1]["TABLE_NAME"] == "Contact"
    mock_connect_ai_metadata["tables"].assert_called_once_with("conn-001", "Salesforce1", "dbo")


def test_get_tables_requires_login(client, mock_connect_ai_metadata):
    """未認証でのテーブル一覧取得は 401 が返ること"""
    resp = client.get(
        "/api/v1/metadata/tables?connection_id=conn-001&catalog_name=Salesforce1&schema_name=dbo"
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# カラム一覧取得
# ---------------------------------------------------------------------------

def test_get_columns_success(client, mock_connect_ai_metadata):
    """ログイン済みユーザーがカラム一覧を取得できること"""
    _register_and_login(client)
    resp = client.get(
        "/api/v1/metadata/columns"
        "?connection_id=conn-001&catalog_name=Salesforce1&schema_name=dbo&table_name=Account"
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert "columns" in data
    assert len(data["columns"]) == 2
    assert data["columns"][0]["COLUMN_NAME"] == "Id"
    assert data["columns"][0]["TYPE_NAME"] == "VARCHAR"
    assert data["columns"][0]["IS_NULLABLE"] == False
    mock_connect_ai_metadata["columns"].assert_called_once_with(
        "conn-001", "Salesforce1", "dbo", "Account"
    )


def test_get_columns_requires_login(client, mock_connect_ai_metadata):
    """未認証でのカラム一覧取得は 401 が返ること"""
    resp = client.get(
        "/api/v1/metadata/columns"
        "?connection_id=conn-001&catalog_name=Salesforce1&schema_name=dbo&table_name=Account"
    )
    assert resp.status_code == 401
