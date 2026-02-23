from pydantic import BaseModel

VALID_OPERATORS = {"=", "<>", "<", ">", "<=", ">=", "LIKE", "IN", "BETWEEN"}


class ConditionSchema(BaseModel):
    column: str
    operator: str
    value: str
    value2: str = ""


class QueryRequestSchema(BaseModel):
    connection_id: str
    catalog_name: str
    schema_name: str
    table_name: str
    columns: list[str] = []
    conditions: list[ConditionSchema] = []
