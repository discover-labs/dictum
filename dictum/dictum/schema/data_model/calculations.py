from typing import Any, Optional

from pydantic import Field

from dictum.schema.data_model.format import Formatted
from dictum.schema.data_model.type import Type


class Displayed(Formatted):
    id: str
    name: str
    description: Optional[str]
    type: Type
    missing: Optional[Any]


class Calculation(Displayed):
    str_expr: str = Field(..., alias="expr")


class Measure(Calculation):
    type: Type = "float"
    metric: bool = True


class Metric(Calculation):
    type: Type = "float"


class Dimension(Calculation):
    union: Optional[str]


class DimensionsUnion(Displayed):
    pass
