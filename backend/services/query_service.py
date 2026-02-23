import time
from flask_login import current_user
from backend.connectai.client import ConnectAIClient
from backend.schemas.query_schema import QueryRequestSchema


def build_query_sql(
    catalog: str,
    schema: str,
    table: str,
    columns: list[str],
    conditions: list[dict],
) -> tuple[str, dict, dict]:
    """
    SELECT 文・パラメータ・パラメータ型を組み立てて返す。

    Returns:
        (sql, params, param_types)
    """
    # SELECT
    select_part = ", ".join(f"[{c}]" for c in columns) if columns else "*"

    # FROM（完全修飾名）
    from_part = f"[{catalog}].[{schema}].[{table}]"

    # WHERE
    params: dict = {}
    param_types: dict = {}
    where_clauses: list[str] = []

    for i, cond in enumerate(conditions):
        col = cond["column"]
        op = cond["operator"]
        val = cond.get("value", "")

        if op in ("=", "<>", "<", ">", "<=", ">=", "LIKE"):
            pname = f"@p{i}"
            params[pname] = val
            param_types[pname] = "VARCHAR"
            where_clauses.append(f"[{col}] {op} {pname}")

        elif op == "IN":
            values = [v.strip() for v in val.split(",")]
            placeholders = []
            for j, v in enumerate(values):
                pname = f"@p{i}_{j}"
                params[pname] = v
                param_types[pname] = "VARCHAR"
                placeholders.append(pname)
            where_clauses.append(f"[{col}] IN ({', '.join(placeholders)})")

        elif op == "BETWEEN":
            p_a, p_b = f"@p{i}_a", f"@p{i}_b"
            params[p_a] = val
            params[p_b] = cond.get("value2", "")
            param_types[p_a] = "VARCHAR"
            param_types[p_b] = "VARCHAR"
            where_clauses.append(f"[{col}] BETWEEN {p_a} AND {p_b}")

    sql = f"SELECT {select_part} FROM {from_part}"
    if where_clauses:
        sql += " WHERE " + " AND ".join(where_clauses)
    sql += " LIMIT 1000"

    return sql, params, param_types


class QueryService:

    def _client(self) -> ConnectAIClient:
        return ConnectAIClient(child_account_id=current_user.connect_ai_account_id)

    def execute_query(self, req: QueryRequestSchema) -> dict:
        """
        クエリを実行し結果を返す。

        Returns:
            {"columns": [...], "rows": [...], "total": N, "elapsed_ms": N}
        """
        sql, params, param_types = build_query_sql(
            req.catalog_name,
            req.schema_name,
            req.table_name,
            req.columns,
            [c.model_dump() for c in req.conditions],
        )
        start = time.time()
        columns, rows = self._client().query_data(
            sql,
            params if params else None,
            param_types if param_types else None,
        )
        elapsed_ms = int((time.time() - start) * 1000)
        return {
            "columns": columns,
            "rows": rows,
            "total": len(rows),
            "elapsed_ms": elapsed_ms,
        }
