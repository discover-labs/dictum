from abc import ABC, abstractmethod
from typing import Literal, Tuple, Union

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


def _issubclass(cls, bases: Union[type, Tuple[type, ...]]):
    if not isinstance(bases, tuple):
        return issubclass(cls, bases)
    for base in bases:
        if issubclass(cls, base):
            return True
    return False


def cls_to_info_type(cls):
    if _issubclass(cls, (PositionFieldDef, LatLongFieldDef, SecondaryFieldDef)):
        return "axis"
    if _issubclass(cls, (FacetEncodingFieldDef, RowColumnEncodingFieldDef)):
        return "header"
    if _issubclass(
        cls,
        (
            ColorGradientFieldDefWithCondition,
            ShapeFieldDefWithCondition,
            NumericFieldDefWithCondition,
            NumericArrayFieldDefWithCondition,
        ),
    ):
        return "legend"
    return None


class AltairEncodingChannelHook(ABC):
    @abstractmethod
    def encoding_fields(self, info: ChannelInfoType) -> dict:
        ...
