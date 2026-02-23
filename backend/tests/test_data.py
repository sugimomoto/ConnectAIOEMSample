"""
データ CRUD API のテスト（テストファースト）
"""
import pytest
from backend.services.data_service import (
    build_select_sql,
    build_count_sql,
    build_insert_sql,
    build_update_sql,
    build_delete_sql,
)


# ---------------------------------------------------------------------------
# ヘルパー
# ---------------------------------------------------------------------------

def _register_and_login(client, email="user@example.com", password="password123", name="Test User"):
    client.post("/api/v1/auth/register", json={"email": email, "password": password, "name": name})
    client.post("/api/v1/auth/login", json={"email": email, "password": password})


_BASE = {
    "connection_id": "conn-001",
    "catalog": "Salesforce1",
    "schema_name": "dbo",
    "table": "Account",
}


# ---------------------------------------------------------------------------
# API テスト
# ---------------------------------------------------------------------------

def test_get_records_success(client, mock_connect_ai_crud):
    """ログイン済みユーザーがレコード一覧を取得できること"""
    _register_and_login(client)
    resp = client.get(
        "/api/v1/data/records",
        query_string={**_BASE, "limit": 20, "offset": 0},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert "columns" in data
    assert "rows" in data
    assert "total" in data
    assert data["columns"] == ["Id", "Name", "Industry"]
    assert len(data["rows"]) == 2


def test_get_records_requires_login(client, mock_connect_ai_crud):
    """未認証でのレコード一覧取得は 401 が返ること"""
    resp = client.get("/api/v1/data/records", query_string=_BASE)
    assert resp.status_code == 401


def test_get_records_missing_param(client, mock_connect_ai_crud):
    """必須パラメータ欠如で 400 が返ること"""
    _register_and_login(client)
    resp = client.get(
        "/api/v1/data/records",
        query_string={"connection_id": "conn-001"},  # catalog, schema_name, table が欠如
    )
    assert resp.status_code == 400


def test_create_record_success(client, mock_connect_ai_crud):
    """正常なレコード作成で 201 + message が返ること"""
    _register_and_login(client)
    resp = client.post("/api/v1/data/records", json={
        **_BASE,
        "data": {"Name": "New Corp", "Industry": "Technology"},
    })
    assert resp.status_code == 201
    assert "message" in resp.get_json()


def test_create_record_requires_login(client, mock_connect_ai_crud):
    """未認証でのレコード作成は 401 が返ること"""
    resp = client.post("/api/v1/data/records", json={
        **_BASE,
        "data": {"Name": "New Corp"},
    })
    assert resp.status_code == 401


def test_update_record_success(client, mock_connect_ai_crud):
    """正常なレコード更新で 200 + message が返ること"""
    _register_and_login(client)
    resp = client.put("/api/v1/data/records", json={
        **_BASE,
        "data": {"Name": "Updated Corp"},
        "where": {"Id": "001xxx"},
    })
    assert resp.status_code == 200
    assert "message" in resp.get_json()


def test_update_record_requires_login(client, mock_connect_ai_crud):
    """未認証でのレコード更新は 401 が返ること"""
    resp = client.put("/api/v1/data/records", json={
        **_BASE,
        "data": {"Name": "Updated Corp"},
        "where": {"Id": "001xxx"},
    })
    assert resp.status_code == 401


def test_delete_record_success(client, mock_connect_ai_crud):
    """正常なレコード削除で 200 + message が返ること"""
    _register_and_login(client)
    resp = client.delete("/api/v1/data/records", json={
        **_BASE,
        "where": {"Id": "001xxx"},
    })
    assert resp.status_code == 200
    assert "message" in resp.get_json()


def test_delete_record_requires_login(client, mock_connect_ai_crud):
    """未認証でのレコード削除は 401 が返ること"""
    resp = client.delete("/api/v1/data/records", json={
        **_BASE,
        "where": {"Id": "001xxx"},
    })
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# SQL 組み立て単体テスト
# ---------------------------------------------------------------------------

def test_build_select_sql():
    """`SELECT *` + `LIMIT N OFFSET M` の SQL が生成されること"""
    sql = build_select_sql("Cat", "Sch", "Tbl", limit=20, offset=40)
    assert "SELECT *" in sql
    assert "FROM [Cat].[Sch].[Tbl]" in sql
    assert "LIMIT 20" in sql
    assert "OFFSET 40" in sql


def test_build_count_sql():
    """`SELECT COUNT(*) AS [cnt]` の SQL が生成されること"""
    sql = build_count_sql("Cat", "Sch", "Tbl")
    assert "COUNT(*)" in sql
    assert "FROM [Cat].[Sch].[Tbl]" in sql


def test_build_insert_sql():
    """`INSERT INTO ... VALUES (@s0, @s1)` + params が生成されること"""
    sql, params, param_types = build_insert_sql(
        "Cat", "Sch", "Tbl",
        data={"Name": "Acme", "Industry": "Tech"},
    )
    assert "INSERT INTO [Cat].[Sch].[Tbl]" in sql
    assert "[Name]" in sql
    assert "[Industry]" in sql
    assert "@s0" in sql
    assert "@s1" in sql
    assert params["@s0"] == "Acme"
    assert params["@s1"] == "Tech"
    assert param_types["@s0"] == "VARCHAR"


def test_build_update_sql():
    """`SET [col] = @s0 WHERE [col] = @w0` + params が生成されること"""
    sql, params, param_types = build_update_sql(
        "Cat", "Sch", "Tbl",
        data={"Name": "New Corp"},
        where={"Id": "001xxx"},
    )
    assert "UPDATE [Cat].[Sch].[Tbl]" in sql
    assert "SET [Name] = @s0" in sql
    assert "WHERE [Id] = @w0" in sql
    assert params["@s0"] == "New Corp"
    assert params["@w0"] == "001xxx"
    assert param_types["@s0"] == "VARCHAR"
    assert param_types["@w0"] == "VARCHAR"


def test_build_delete_sql():
    """`DELETE FROM ... WHERE [col] = @w0` + params が生成されること"""
    sql, params, param_types = build_delete_sql(
        "Cat", "Sch", "Tbl",
        where={"Id": "001xxx"},
    )
    assert "DELETE FROM [Cat].[Sch].[Tbl]" in sql
    assert "WHERE [Id] = @w0" in sql
    assert params["@w0"] == "001xxx"
    assert param_types["@w0"] == "VARCHAR"
