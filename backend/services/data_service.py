from flask_login import current_user
from backend.connectai.client import ConnectAIClient
from backend.connectai.exceptions import ConnectAIError
from backend.schemas.data_schema import (
    RecordListSchema,
    RecordWriteSchema,
    RecordUpdateSchema,
    RecordDeleteSchema,
)


def build_select_sql(
    catalog: str,
    schema: str,
    table: str,
    limit: int,
    offset: int,
) -> str:
    limit = max(1, min(limit, 100))
    return f"SELECT * FROM [{catalog}].[{schema}].[{table}] LIMIT {limit} OFFSET {offset}"


def build_count_sql(catalog: str, schema: str, table: str) -> str:
    return f"SELECT COUNT(*) AS [cnt] FROM [{catalog}].[{schema}].[{table}]"


def build_insert_sql(
    catalog: str,
    schema: str,
    table: str,
    data: dict[str, str],
) -> tuple[str, dict, dict]:
    params: dict = {}
    param_types: dict = {}
    placeholders = []
    for i, (col, val) in enumerate(data.items()):
        pname = f"@s{i}"
        params[pname] = val
        param_types[pname] = "VARCHAR"
        placeholders.append(pname)
    col_part = ", ".join(f"[{c}]" for c in data)
    val_part = ", ".join(placeholders)
    sql = f"INSERT INTO [{catalog}].[{schema}].[{table}] ({col_part}) VALUES ({val_part})"
    return sql, params, param_types


def build_update_sql(
    catalog: str,
    schema: str,
    table: str,
    data: dict[str, str],
    where: dict[str, str],
) -> tuple[str, dict, dict]:
    params: dict = {}
    param_types: dict = {}
    set_parts = []
    for i, (col, val) in enumerate(data.items()):
        pname = f"@s{i}"
        params[pname] = val
        param_types[pname] = "VARCHAR"
        set_parts.append(f"[{col}] = {pname}")
    where_parts = []
    for i, (col, val) in enumerate(where.items()):
        pname = f"@w{i}"
        params[pname] = val
        param_types[pname] = "VARCHAR"
        where_parts.append(f"[{col}] = {pname}")
    sql = (
        f"UPDATE [{catalog}].[{schema}].[{table}]"
        f" SET {', '.join(set_parts)}"
        f" WHERE {' AND '.join(where_parts)}"
    )
    return sql, params, param_types


def build_delete_sql(
    catalog: str,
    schema: str,
    table: str,
    where: dict[str, str],
) -> tuple[str, dict, dict]:
    params: dict = {}
    param_types: dict = {}
    where_parts = []
    for i, (col, val) in enumerate(where.items()):
        pname = f"@w{i}"
        params[pname] = val
        param_types[pname] = "VARCHAR"
        where_parts.append(f"[{col}] = {pname}")
    sql = (
        f"DELETE FROM [{catalog}].[{schema}].[{table}]"
        f" WHERE {' AND '.join(where_parts)}"
    )
    return sql, params, param_types


class DataService:

    def _client(self) -> ConnectAIClient:
        return ConnectAIClient(child_account_id=current_user.connect_ai_account_id)

    def list_records(self, req: RecordListSchema) -> dict:
        client = self._client()

        # 総件数取得（失敗時は -1）
        total = -1
        try:
            count_sql = build_count_sql(req.catalog, req.schema_name, req.table)
            _, count_rows = client.query_data(count_sql)
            if count_rows and count_rows[0]:
                total = int(count_rows[0][0])
        except (ConnectAIError, ValueError, IndexError):
            pass

        # レコード取得
        sql = build_select_sql(req.catalog, req.schema_name, req.table, req.limit, req.offset)
        columns, rows = client.query_data(sql)

        return {
            "columns": columns,
            "rows": rows,
            "total": total,
            "limit": req.limit,
            "offset": req.offset,
        }

    def create_record(self, req: RecordWriteSchema) -> dict:
        sql, params, param_types = build_insert_sql(
            req.catalog, req.schema_name, req.table, req.data
        )
        self._client().query_data(sql, params, param_types)
        return {"message": "Record created successfully."}

    def update_record(self, req: RecordUpdateSchema) -> dict:
        if not req.where:
            raise ValueError("WHERE condition is required for UPDATE.")
        sql, params, param_types = build_update_sql(
            req.catalog, req.schema_name, req.table, req.data, req.where
        )
        self._client().query_data(sql, params, param_types)
        return {"message": "Record updated successfully."}

    def delete_record(self, req: RecordDeleteSchema) -> dict:
        if not req.where:
            raise ValueError("WHERE condition is required for DELETE.")
        sql, params, param_types = build_delete_sql(
            req.catalog, req.schema_name, req.table, req.where
        )
        self._client().query_data(sql, params, param_types)
        return {"message": "Record deleted successfully."}
