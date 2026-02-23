import pytest
from unittest.mock import patch
from backend.app import create_app
from backend.models import db as _db


@pytest.fixture
def app():
    """テスト用Flaskアプリ（in-memory SQLite）"""
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "test-secret-key",
        "WTF_CSRF_ENABLED": False,
        "CONNECT_AI_PARENT_ACCOUNT_ID": "test-parent-account-id",
        "CONNECT_AI_PRIVATE_KEY_PATH": "backend/keys/private.key",
    })
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def mock_connect_ai():
    """Connect AI Account API をモックする（外部APIへの依存を排除）"""
    with patch("backend.connectai.client.ConnectAIClient.create_account") as mock:
        mock.return_value = "mock-child-account-id-001"
        yield mock


@pytest.fixture
def mock_connect_ai_metadata():
    """Connect AI メタデータ関連 API をモックする"""
    with patch("backend.connectai.client.ConnectAIClient.get_catalogs") as mock_catalogs, \
         patch("backend.connectai.client.ConnectAIClient.get_schemas") as mock_schemas, \
         patch("backend.connectai.client.ConnectAIClient.get_tables") as mock_tables, \
         patch("backend.connectai.client.ConnectAIClient.get_columns") as mock_columns:

        mock_catalogs.return_value = [
            {"TABLE_CATALOG": "Salesforce1", "DATA_SOURCE": "Salesforce", "CONNECTION_ID": "conn-001"},
        ]
        mock_schemas.return_value = [
            {"TABLE_CATALOG": "Salesforce1", "TABLE_SCHEMA": "dbo"},
        ]
        mock_tables.return_value = [
            {"TABLE_CATALOG": "Salesforce1", "TABLE_SCHEMA": "dbo", "TABLE_NAME": "Account", "TABLE_TYPE": "TABLE", "REMARKS": None},
            {"TABLE_CATALOG": "Salesforce1", "TABLE_SCHEMA": "dbo", "TABLE_NAME": "Contact", "TABLE_TYPE": "TABLE", "REMARKS": None},
        ]
        mock_columns.return_value = [
            {"TABLE_CATALOG": "Salesforce1", "TABLE_SCHEMA": "dbo", "TABLE_NAME": "Account", "COLUMN_NAME": "Id", "TYPE_NAME": "VARCHAR", "IS_NULLABLE": False},
            {"TABLE_CATALOG": "Salesforce1", "TABLE_SCHEMA": "dbo", "TABLE_NAME": "Account", "COLUMN_NAME": "Name", "TYPE_NAME": "VARCHAR", "IS_NULLABLE": True},
        ]
        yield {
            "catalogs": mock_catalogs,
            "schemas": mock_schemas,
            "tables": mock_tables,
            "columns": mock_columns,
        }


@pytest.fixture
def mock_connect_ai_query():
    """Connect AI クエリ API をモックする"""
    with patch("backend.connectai.client.ConnectAIClient.query_data") as mock_query:
        mock_query.return_value = (
            ["Id", "Name"],
            [["001", "John Doe"], ["002", "Jane"]],
        )
        yield mock_query


@pytest.fixture
def mock_connect_ai_crud():
    """Connect AI クエリ API（SELECT / DML 両用）をモックする"""
    with patch("backend.connectai.client.ConnectAIClient.query_data") as mock:
        mock.return_value = (
            ["Id", "Name", "Industry"],
            [
                ["001", "Acme Corp", "Technology"],
                ["002", "Widget Co", "Manufacturing"],
            ],
        )
        yield mock


@pytest.fixture
def second_user_client(app):
    """2人目のユーザーを登録・ログインした専用クライアントを返す（ユーザー分離テスト用）"""
    client2 = app.test_client()
    client2.post("/api/v1/auth/register", json={
        "email": "other@example.com",
        "password": "password123",
        "name": "Other User",
    })
    client2.post("/api/v1/auth/login", json={
        "email": "other@example.com",
        "password": "password123",
    })
    return client2


@pytest.fixture
def mock_connect_ai_connections():
    """Connect AI コネクション関連 API をモックする"""
    with patch("backend.connectai.client.ConnectAIClient.get_datasources") as mock_ds, \
         patch("backend.connectai.client.ConnectAIClient.get_connections") as mock_list, \
         patch("backend.connectai.client.ConnectAIClient.create_connection") as mock_create, \
         patch("backend.connectai.client.ConnectAIClient.delete_connection") as mock_delete:

        mock_ds.return_value = [{"name": "Salesforce"}, {"name": "QuickBooks"}]
        mock_list.return_value = [
            {"id": "conn-001", "name": "My SF", "dataSource": "Salesforce", "status": "active"}
        ]
        mock_create.return_value = "https://cloud.cdata.com/connect/auth/mock-token"
        mock_delete.return_value = None
        yield {
            "datasources": mock_ds,
            "list": mock_list,
            "create": mock_create,
            "delete": mock_delete,
        }
