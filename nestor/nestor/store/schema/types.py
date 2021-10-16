from enum import Enum

Expression = str
Identifier = str  # TODO: make these actual types


class DimensionType(str, Enum):
    time = "time"
    continuous = "continuous"
    ordinal = "ordinal"
    nominal = "nominal"
