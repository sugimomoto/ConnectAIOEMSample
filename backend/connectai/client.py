import json
import threading
import time

import requests
from flask import current_app
from flask_login import current_user
from .jwt import generate_connect_ai_jwt
from .exceptions import ConnectAIError


def _save_log_async(app, user_id: int, method: str, endpoint: str,
                    request_body, response_body, status_code: int, elapsed_ms: int) -> None:
    """API ログを DB にバックグラウンドで保存する（メイン処理をブロックしない）"""
    def _save():
        with app.app_context():
            try:
                from backend.models.api_log import ApiLog
                from backend.models import db
                log = ApiLog(
                    user_id=user_id,
                    method=method,
                    endpoint=endpoint,
                    request_body=(
                        json.dumps(request_body, ensure_ascii=False)
                        if request_body is not None else None
                    ),
                    response_body=(
                        json.dumps(response_body, ensure_ascii=False)
                        if response_body is not None else None
                    ),
                    status_code=status_code,
                    elapsed_ms=elapsed_ms,
                )
                db.session.add(log)
                db.session.commit()
            except Exception:
                pass  # ログ失敗はサイレントに無視
    threading.Thread(target=_save, daemon=True).start()


class ConnectAIClient:
    """
    Connect AI HTTP API クライアント。
    各メソッド呼び出し時に JWT を生成してリクエストに付与する。
    """

    def __init__(self, child_account_id: str | None):
        self.base_url = current_app.config["CONNECT_AI_BASE_URL"]
        self.parent_account_id = current_app.config["CONNECT_AI_PARENT_ACCOUNT_ID"]
        # 子アカウント未作成の場合は空文字列を使う（Account API 呼び出し時）
        self.subject_id = child_account_id if child_account_id is not None else ""

    def _headers(self) -> dict:
        token = generate_connect_ai_jwt(self.parent_account_id, self.subject_id)
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    def _log(self, path: str, method: str, request_body, response_body,
             status_code: int, start: float) -> None:
        """API 呼び出し結果をバックグラウンドスレッドで DB に記録する。未認証時はスキップ。"""
        try:
            if not current_user.is_authenticated:
                return
            user_id = current_user.id
            app = current_app._get_current_object()
            elapsed_ms = int((time.monotonic() - start) * 1000)
            _save_log_async(
                app=app,
                user_id=user_id,
                method=method,
                endpoint=path,
                request_body=request_body,
                response_body=response_body,
                status_code=status_code,
                elapsed_ms=elapsed_ms,
            )
        except Exception:
            pass  # ログ処理のエラーは本体に伝播させない

    def _get(self, path: str, params: dict | None = None) -> dict:
        from urllib.parse import urlencode
        url = f"{self.base_url}{path}"
        log_path = f"{path}?{urlencode(params)}" if params else path
        start = time.monotonic()
        try:
            resp = requests.get(url, headers=self._headers(), params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            self._log(log_path, "GET", None, data, resp.status_code, start)
            return data
        except requests.HTTPError as e:
            self._log(log_path, "GET", None, {"error": e.response.text}, e.response.status_code, start)
            raise ConnectAIError(f"HTTP {e.response.status_code}: {e.response.text}") from e
        except requests.exceptions.JSONDecodeError as e:
            raise ConnectAIError(f"Invalid JSON (HTTP {resp.status_code}): {resp.text[:500]!r}") from e
        except requests.RequestException as e:
            raise ConnectAIError(f"Request failed: {e}") from e

    @staticmethod
    def _rows_to_dicts(result: dict) -> list[dict]:
        """SQL形式のレスポンス（schema + rows）を dict の一覧に変換する。"""
        columns = [col["columnName"] for col in result["schema"]]
        return [dict(zip(columns, row)) for row in result["rows"]]

    def _delete(self, path: str) -> None:
        url = f"{self.base_url}{path}"
        start = time.monotonic()
        try:
            resp = requests.delete(url, headers=self._headers(), timeout=30)
            resp.raise_for_status()
            self._log(path, "DELETE", None, None, resp.status_code, start)
        except requests.HTTPError as e:
            self._log(path, "DELETE", None, {"error": e.response.text}, e.response.status_code, start)
            raise ConnectAIError(f"HTTP {e.response.status_code}: {e.response.text}") from e
        except requests.RequestException as e:
            raise ConnectAIError(f"Request failed: {e}") from e

    def _post(self, path: str, payload: dict) -> dict:
        url = f"{self.base_url}{path}"
        start = time.monotonic()
        try:
            resp = requests.post(url, json=payload, headers=self._headers(), timeout=30)
            resp.raise_for_status()
            data = resp.json()
            self._log(path, "POST", payload, data, resp.status_code, start)
            return data
        except requests.HTTPError as e:
            self._log(path, "POST", payload, {"error": e.response.text}, e.response.status_code, start)
            raise ConnectAIError(
                f"HTTP {e.response.status_code}: {e.response.text} "
                f"| Request: POST {path} | Payload: {json.dumps(payload, ensure_ascii=False)}"
            ) from e
        except requests.exceptions.JSONDecodeError as e:
            raise ConnectAIError(f"Invalid JSON (HTTP {resp.status_code}): {resp.text[:500]!r}") from e
        except requests.RequestException as e:
            raise ConnectAIError(f"Request failed: {e}") from e

    def create_account(self, external_id: str) -> str:
        """
        子アカウントを作成し、ChildAccountId を返す。

        Args:
            external_id: アプリ側のユーザーID（文字列）
        Returns:
            ChildAccountId（Connect AI が発行する accountId）
        """
        data = self._post("/poweredby/account/create", {"externalId": external_id})
        return data["accountId"]

    def get_datasources(self) -> list[dict]:
        """
        利用可能なデータソース一覧を返す。

        Returns:
            [{"name": "Salesforce", ...}, ...]
        """
        data = self._get("/poweredby/sources/list")
        return data.get("dataSources", data) if isinstance(data, dict) else data

    def get_connections(self) -> list[dict]:
        """
        ChildAccountId に紐づくコネクション一覧を返す。

        Returns:
            [{"id": "...", "name": "...", "dataSource": "...", "status": "..."}, ...]
        """
        data = self._get("/poweredby/connection/list")
        return data.get("connections", data) if isinstance(data, dict) else data

    def create_connection(self, name: str, data_source: str, redirect_url: str) -> str:
        """
        コネクションを作成し、Connect AI の認証画面 URL を返す。

        Args:
            name: コネクション名
            data_source: データソース種別（例: "Salesforce"）
            redirect_url: 認証完了後のリダイレクト先 URL
        Returns:
            Connect AI の認証画面 URL
        """
        data = self._post("/poweredby/connection/create", {
            "name": name,
            "dataSource": data_source,
            "redirectURL": redirect_url,
        })
        return data["redirectURL"]

    def delete_connection(self, connection_id: str) -> None:
        """
        コネクションを削除する。

        Args:
            connection_id: Connect AI 側のコネクション ID
        """
        self._delete(f"/poweredby/connection/delete/{connection_id}")

    # Connect AI dataType 定数（SQL TYPE_NAME → dataType 番号）
    _TYPE_NAME_TO_DATA_TYPE: dict[str, int] = {
        "BINARY": 1,
        "VARCHAR": 5,
        "TINYINT": 6,
        "SMALLINT": 7,
        "INTEGER": 8,
        "INT": 8,
        "BIGINT": 9,
        "FLOAT": 10,
        "DOUBLE": 11,
        "DECIMAL": 12,
        "NUMERIC": 13,
        "BOOLEAN": 14,
        "DATE": 15,
        "TIME": 16,
        "TIMESTAMP": 17,
        "UUID": 18,
    }

    def query_data(
        self,
        sql: str,
        params: dict | None = None,
        param_types: dict | None = None,
    ) -> tuple[list[str], list[list]]:
        """
        SQL を実行し、(column_names, rows) を返す。

        params の各値は {"dataType": N, "value": "..."} 形式に変換して送信する。

        Returns:
            (["Id", "Name", ...], [["001", "John"], ...])
        """
        payload: dict = {"query": sql}
        if params:
            formatted: dict = {}
            for key, value in params.items():
                type_name = (param_types or {}).get(key, "VARCHAR").upper()
                data_type = self._TYPE_NAME_TO_DATA_TYPE.get(type_name, 5)
                formatted[key] = {"dataType": data_type, "value": str(value)}
            payload["parameters"] = formatted
        sql_context = f" | [Sent] SQL: {sql} | Parameters: {json.dumps(params, ensure_ascii=False)}"
        try:
            data = self._post("/query", payload)
        except ConnectAIError as e:
            raise ConnectAIError(f"{e}{sql_context}") from e
        try:
            result = data["results"][0]
            # DML (INSERT/UPDATE/DELETE) returns {"affectedRows": N} without schema/rows
            if "schema" not in result:
                return [], []
            columns = [col["columnName"] for col in result["schema"]]
            rows = result["rows"]
        except (KeyError, TypeError, IndexError) as e:
            raise ConnectAIError(
                f"Unexpected response ({type(e).__name__}: {e}): "
                f"{json.dumps(data, ensure_ascii=False)}{sql_context}"
            ) from e
        return columns, rows

    def get_catalogs(self) -> list[dict]:
        """
        カタログ一覧を返す。

        Returns:
            [{"TABLE_CATALOG": "...", "DATA_SOURCE": "...", "CONNECTION_ID": "..."}, ...]
        """
        data = self._get("/catalogs")
        return self._rows_to_dicts(data["results"][0])

    def get_schemas(self, catalog_name: str) -> list[dict]:
        """
        スキーマ一覧を返す。

        Returns:
            [{"TABLE_CATALOG": "...", "TABLE_SCHEMA": "..."}, ...]
        """
        data = self._get("/schemas", params={"catalogName": catalog_name})
        return self._rows_to_dicts(data["results"][0])

    def get_tables(self, catalog_name: str, schema_name: str) -> list[dict]:
        """
        テーブル一覧を返す。

        Returns:
            [{"TABLE_CATALOG": "...", "TABLE_SCHEMA": "...", "TABLE_NAME": "...", "TABLE_TYPE": "...", "REMARKS": ...}, ...]
        """
        data = self._get("/tables", params={
            "catalogName": catalog_name,
            "schemaName": schema_name,
        })
        return self._rows_to_dicts(data["results"][0])

    def get_columns(self, catalog_name: str, schema_name: str, table_name: str) -> list[dict]:
        """
        カラム一覧を返す。

        Returns:
            [{"COLUMN_NAME": "...", "TYPE_NAME": "...", "IS_NULLABLE": bool, ...}, ...]
        """
        data = self._get("/columns", params={
            "catalogName": catalog_name,
            "schemaName": schema_name,
            "tableName": table_name,
        })
        return self._rows_to_dicts(data["results"][0])
