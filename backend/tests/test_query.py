"""
クエリ API のテスト（テストファースト）

各テストは実装前に記述しているため、実装完了前は FAIL する。
"""
import pytest
from backend.services.query_service import build_query_sql


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
# API テスト
# ---------------------------------------------------------------------------

def test_execute_query_success(client, mock_connect_ai_query):
    """ログイン済みユーザーがクエリを実行して結果を取得できること"""
    _register_and_login(client)
    resp = client.post("/api/v1/query", json={
        "connection_id": "conn-001",
        "catalog_name": "Salesforce1",
        "schema_name": "dbo",
        "table_name": "Account",
        "columns": ["Id", "Name"],
        "conditions": [],
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["columns"] == ["Id", "Name"]
    assert len(data["rows"]) == 2
    assert data["rows"][0] == ["001", "John Doe"]
    assert data["total"] == 2
    assert "elapsed_ms" in data


def test_execute_query_requires_login(client, mock_connect_ai_query):
    """未認証でのクエリ実行は 401 が返ること"""
    resp = client.post("/api/v1/query", json={
        "connection_id": "conn-001",
        "catalog_name": "Salesforce1",
        "schema_name": "dbo",
        "table_name": "Account",
    })
    assert resp.status_code == 401


def test_execute_query_missing_param(client, mock_connect_ai_query):
    """必須パラメータ欠如で 400 が返ること"""
    _register_and_login(client)
    resp = client.post("/api/v1/query", json={
        "connection_id": "conn-001",
        # catalog_name, schema_name, table_name が欠如
    })
    assert resp.status_code == 400


def test_execute_query_select_star(client, mock_connect_ai_query):
    """`columns=[]` のとき query_data が SELECT * で呼ばれること"""
    _register_and_login(client)
    client.post("/api/v1/query", json={
        "connection_id": "conn-001",
        "catalog_name": "Salesforce1",
        "schema_name": "dbo",
        "table_name": "Account",
        "columns": [],
        "conditions": [],
    })
    called_sql = mock_connect_ai_query.call_args[0][0]
    assert "SELECT *" in called_sql


def test_execute_query_with_conditions(client, mock_connect_ai_query):
    """WHERE 条件あり時に query_data が適切な引数で呼ばれること"""
    _register_and_login(client)
    client.post("/api/v1/query", json={
        "connection_id": "conn-001",
        "catalog_name": "Salesforce1",
        "schema_name": "dbo",
        "table_name": "Account",
        "columns": ["Id", "Name"],
        "conditions": [
            {"column": "Name", "operator": "LIKE", "value": "%John%"},
        ],
    })
    called_sql = mock_connect_ai_query.call_args[0][0]
    assert "WHERE" in called_sql
    assert "LIKE" in called_sql


def test_execute_query_connect_ai_error(client, mock_connect_ai_query):
    """Connect AI エラー時に 502 が返ること"""
    from backend.connectai.exceptions import ConnectAIError
    mock_connect_ai_query.side_effect = ConnectAIError("connection timeout")
    _register_and_login(client)
    resp = client.post("/api/v1/query", json={
        "connection_id": "conn-001",
        "catalog_name": "Salesforce1",
        "schema_name": "dbo",
        "table_name": "Account",
    })
    assert resp.status_code == 502


# ---------------------------------------------------------------------------
# SQL 組み立て単体テスト
# ---------------------------------------------------------------------------

def test_build_sql_no_conditions():
    """`conditions=[]` で WHERE なし + LIMIT 1000 の SQL が生成されること"""
    sql, params, param_types = build_query_sql(
        "Cat", "Sch", "Tbl", ["Id", "Name"], []
    )
    assert "SELECT [Id], [Name]" in sql
    assert "FROM [Cat].[Sch].[Tbl]" in sql
    assert "WHERE" not in sql
    assert "LIMIT 1000" in sql
    assert params == {}


def test_build_sql_single_condition():
    """`=` 演算子で WHERE 句とパラメータが生成されること"""
    sql, params, param_types = build_query_sql(
        "Cat", "Sch", "Tbl", [], [{"column": "Id", "operator": "=", "value": "001", "value2": ""}]
    )
    assert "WHERE [Id] = @p0" in sql
    assert params["@p0"] == "001"


def test_build_sql_like():
    """`LIKE` 演算子が SQL に含まれること"""
    sql, params, _ = build_query_sql(
        "Cat", "Sch", "Tbl", [],
        [{"column": "Name", "operator": "LIKE", "value": "%John%", "value2": ""}]
    )
    assert "[Name] LIKE @p0" in sql
    assert params["@p0"] == "%John%"


def test_build_sql_in():
    """`IN` 演算子でカンマ分割した複数パラメータが生成されること"""
    sql, params, _ = build_query_sql(
        "Cat", "Sch", "Tbl", [],
        [{"column": "Status", "operator": "IN", "value": "Active,Inactive", "value2": ""}]
    )
    assert "[Status] IN" in sql
    assert "@p0_0" in sql
    assert "@p0_1" in sql
    assert params["@p0_0"] == "Active"
    assert params["@p0_1"] == "Inactive"


def test_build_sql_between():
    """`BETWEEN` 演算子で `@pi_a` / `@pi_b` パラメータが生成されること"""
    sql, params, _ = build_query_sql(
        "Cat", "Sch", "Tbl", [],
        [{"column": "Age", "operator": "BETWEEN", "value": "20", "value2": "30"}]
    )
    assert "[Age] BETWEEN @p0_a AND @p0_b" in sql
    assert params["@p0_a"] == "20"
    assert params["@p0_b"] == "30"


def test_build_sql_select_columns():
    """指定カラムのみ SELECT 句に含まれること"""
    sql, _, _ = build_query_sql("Cat", "Sch", "Tbl", ["Id", "Name", "Age"], [])
    assert "SELECT [Id], [Name], [Age]" in sql
    assert "SELECT *" not in sql
