from flask import current_app
from flask_login import current_user
from backend.connectai.client import ConnectAIClient
from backend.connectai.exceptions import ConnectAIError


class ConnectionService:

    def _client(self) -> ConnectAIClient:
        """ログイン中ユーザーの ChildAccountId で Connect AI クライアントを生成する。"""
        return ConnectAIClient(child_account_id=current_user.connect_ai_account_id)

    def get_datasources(self) -> list[dict]:
        """データソース一覧を Connect AI から取得する。
        データソース一覧はユーザー固有ではないため、sub="" の親アカウントレベルで取得する。
        """
        return ConnectAIClient(child_account_id=None).get_datasources()

    def get_connections(self) -> list[dict]:
        """コネクション一覧を Connect AI から取得する。"""
        return self._client().get_connections()

    def create_connection(self, name: str, data_source: str) -> str:
        """
        コネクションを作成し、Connect AI の認証画面 URL を返す。

        Raises:
            ValueError: connect_ai_account_id が未設定の場合
            ConnectAIError: Connect AI API 呼び出し失敗
        """
        if not current_user.connect_ai_account_id:
            raise ValueError("Connect AI アカウントが未設定です。管理者にお問い合わせください。")

        redirect_url = f"{current_app.config['APP_BASE_URL']}/callback"
        return self._client().create_connection(name, data_source, redirect_url)

    def delete_connection(self, connection_id: str) -> None:
        """
        Connect AI 側のコネクションを削除する。

        Raises:
            ConnectAIError: Connect AI API 呼び出し失敗
        """
        self._client().delete_connection(connection_id)
