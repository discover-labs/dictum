import functools
from abc import ABC, abstractmethod
from typing import Literal

from altair import (
    ColorGradientFieldDefWithCondition,
    FacetEncodingFieldDef,
    LatLongFieldDef,
    NumericArrayFieldDefWithCondition,
    NumericFieldDefWithCondition,
    PositionFieldDef,
    RowColumnEncodingFieldDef,
    SecondaryFieldDef,
    ShapeFieldDefWithCondition,
)

ChannelInfoType = Literal["axis", "legend", "header", None]


def cls_to_into_type(fn):
    @functools.wraps(fn)
    def wrapped(self, cls):
        if issubclass(cls, (PositionFieldDef, LatLongFieldDef, SecondaryFieldDef)):
            return fn(self, "axis")
        if issubclass(cls, (FacetEncodingFieldDef, RowColumnEncodingFieldDef)):
            return fn(self, "header")
        if issubclass(
            cls,
            (
                ColorGradientFieldDefWithCondition,
                ShapeFieldDefWithCondition,
                NumericFieldDefWithCondition,
                NumericArrayFieldDefWithCondition,
            ),
        ):
            return fn(self, "legend")
        return fn(self, None)

    return wrapped


class AltairEncodingChannelHook(ABC):
    def __init_subclass__(cls):
        cls.encoding_fields = cls_to_into_type(cls.encoding_fields)

    @abstractmethod
    def encoding_fields(self, info: ChannelInfoType) -> dict:
        ...
