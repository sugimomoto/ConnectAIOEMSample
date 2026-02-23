from pydantic import BaseModel


class RecordListSchema(BaseModel):
    connection_id: str
    catalog: str
    schema_name: str
    table: str
    limit: int = 20
    offset: int = 0


class RecordWriteSchema(BaseModel):
    connection_id: str
    catalog: str
    schema_name: str
    table: str
    data: dict[str, str]


class RecordUpdateSchema(RecordWriteSchema):
    where: dict[str, str]


class RecordDeleteSchema(BaseModel):
    connection_id: str
    catalog: str
    schema_name: str
    table: str
    where: dict[str, str]
