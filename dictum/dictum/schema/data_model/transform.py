from typing import Optional

from pydantic import BaseModel, Field

from dictum.schema.data_model.format import Format
from dictum.schema.data_model.type import Type


class Transform(BaseModel):
    id: str
    name: str
    description: Optional[str]
    args: list = []
    str_expr: str = Field(..., alias="expr")
    format: Optional[Format]
    return_type: Optional[Type]
