from pydantic import BaseModel


class CreateConnectionSchema(BaseModel):
    name: str
    data_source: str
