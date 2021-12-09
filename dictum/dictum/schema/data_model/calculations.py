from typing import Any, Optional

from pydantic import BaseModel, Field, root_validator

from dictum.schema.data_model.format import Format, FormatConfig
from dictum.schema.data_model.type import Type


class Displayed(BaseModel):
    id: str
    name: str
    description: Optional[str]
    type: Type
    format: Optional[Format]
    missing: Optional[Any]

    @staticmethod
    def get_default_format(type: Type) -> Optional[FormatConfig]:
        if type in {"int", "float"}:
            return FormatConfig(kind="number")
        if type in {"date", "datetime"}:
            return FormatConfig(kind=type)

    @root_validator
    def set_default_format(cls, values):
        fmt = values.get("format")
        if fmt is None:
            values["format"] = cls.get_default_format(values.get("type", "float"))
        if isinstance(fmt, str):
            values["format"] = FormatConfig(kind=fmt)
        return values


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
