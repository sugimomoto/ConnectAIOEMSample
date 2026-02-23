from flask_login import current_user
from backend.connectai.client import ConnectAIClient
from backend.connectai.exceptions import ConnectAIError


class MetadataService:

    def _client(self) -> ConnectAIClient:
        """ログイン中ユーザーの ChildAccountId で Connect AI クライアントを生成する。"""
        return ConnectAIClient(child_account_id=current_user.connect_ai_account_id)

    def get_catalogs(self) -> list[dict]:
        """カタログ一覧を Connect AI から取得する。"""
        return self._client().get_catalogs()

    def get_schemas(self, catalog_name: str) -> list[dict]:
        """スキーマ一覧を Connect AI から取得する。"""
        return self._client().get_schemas(catalog_name)

    def get_tables(self, catalog_name: str, schema_name: str) -> list[dict]:
        """テーブル一覧を Connect AI から取得する。"""
        return self._client().get_tables(catalog_name, schema_name)

    def get_columns(self, catalog_name: str, schema_name: str, table_name: str) -> list[dict]:
        """カラム一覧を Connect AI から取得する。"""
        return self._client().get_columns(catalog_name, schema_name, table_name)
