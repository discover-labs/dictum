from abc import ABC, abstractmethod
from typing import Optional

from altair import (
    X2,
    Y2,
    Angle,
    Color,
    Column,
    Detail,
    Facet,
    Fill,
    FillOpacity,
    Href,
    Key,
    Latitude,
    Latitude2,
    Longitude,
    Longitude2,
    Order,
    Radius,
    Row,
    Shape,
    Size,
    Stroke,
    StrokeDash,
    StrokeOpacity,
    StrokeWidth,
    Text,
    Theta,
    Theta2,
    Tooltip,
    X,
    XError,
    XError2,
    Y,
    YError,
    YError2,
)

axis = {
    Latitude,
    Longitude,
    X,
    XError,
    Y,
    YError,
}
legend = {
    Color,
    Angle,
    Fill,
    FillOpacity,
    Radius,
    Shape,
    Size,
    Stroke,
    StrokeDash,
    StrokeOpacity,
    StrokeWidth,
}
header = {Column, Row, Facet}
none = {
    Detail,
    Href,
    Key,
    Text,
    Theta,
    Tooltip,
    Order,
}
field_only = {
    Theta2,
    YError2,
    X2,
    Y2,
    Latitude2,
    Longitude2,
    XError2,
}


class AltairEncodingChannelHook(ABC):
    @abstractmethod
    def encoding_fields(self, cls: Optional[type] = None) -> dict:
        ...


def filter_fields(cls, fields: dict):
    keys = ["field", "type"]
    if cls in axis:
        keys.append("axis")
    if cls in legend:
        keys.append("legend")
    if cls in header:
        keys.append("header")
    if cls in field_only:
        keys.remove("type")
    return {k: fields[k] for k in keys if k in fields}
