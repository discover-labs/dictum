from optparse import Option
from typing import Any, Optional

from pydantic import Field

from dictum.schema.model.format import Formatted
from dictum.schema.model.type import Type


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
    metric: bool = False
    str_filter: Optional[str] = Field(alias="filter")


class Metric(Calculation):
    type: Type = "float"
    table: Optional[str]
    filter: Optional[str]


class Dimension(Calculation):
    union: Optional[str]


class DetachedDimension(Dimension):
    """Just a dimension not defined on a table, the user has to explicitly
    specify which table it is.
    """

    table: str


class DimensionsUnion(Displayed):
    pass
