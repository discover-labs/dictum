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
    X2,
    Y2,
    Latitude,
    Latitude2,
    Longitude,
    Longitude2,
    X,
    XError,
    XError2,
    Y,
    YError,
    YError2,
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
    Theta2,
    Tooltip,
    Order,
}


def cls_to_info_type(cls):
    if cls in axis:
        return "axis"
    if cls in header:
        return "header"
    if cls in legend:
        return "legend"
    return None


class AltairEncodingChannelHook(ABC):
    @abstractmethod
    def encoding_fields(self, cls: Optional[type] = None) -> dict:
        ...
