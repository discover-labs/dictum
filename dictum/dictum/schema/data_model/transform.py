from typing import Optional

from pydantic import Field

from dictum.schema.data_model.format import Formatted
from dictum.schema.data_model.type import Type


class Transform(Formatted):
    id: str
    name: str
    description: Optional[str]
    args: list = []
    str_expr: str = Field(..., alias="expr")
    return_type: Optional[Type]
