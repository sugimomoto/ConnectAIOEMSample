from flask_login import current_user
from backend.connectai.client import ConnectAIClient
from backend.connectai.exceptions import ConnectAIError


class MetadataService:

    def _client(self) -> ConnectAIClient:
        """ログイン中ユーザーの ChildAccountId で Connect AI クライアントを生成する。"""
        return ConnectAIClient(child_account_id=current_user.connect_ai_account_id)

    def get_catalogs(self, connection_id: str) -> list[dict]:
        """カタログ一覧を Connect AI から取得する。"""
        return self._client().get_catalogs(connection_id)

    def get_schemas(self, connection_id: str, catalog_name: str) -> list[dict]:
        """スキーマ一覧を Connect AI から取得する。"""
        return self._client().get_schemas(connection_id, catalog_name)

    def get_tables(self, connection_id: str, catalog_name: str, schema_name: str) -> list[dict]:
        """テーブル一覧を Connect AI から取得する。"""
        return self._client().get_tables(connection_id, catalog_name, schema_name)

    def get_columns(self, connection_id: str, catalog_name: str, schema_name: str, table_name: str) -> list[dict]:
        """カラム一覧を Connect AI から取得する。"""
        return self._client().get_columns(connection_id, catalog_name, schema_name, table_name)
