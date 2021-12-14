import altair
import altair.utils
import pandas as pd
from altair.utils import update_nested
from altair.utils.data import to_values

from dictum.project.altair.data import DictumData
from dictum.project.altair.encoding import AltairEncodingChannelHook
from dictum.project.altair.mixins import BaseMixin

default_infer_encoding_types = altair.utils.infer_encoding_types


def infer_encoding_types(args, kwargs, channels):
    # Construct a dictionary of channel type to encoding name
    channel_objs = (getattr(channels, name) for name in dir(channels))
    channel_objs = (
        c
        for c in channel_objs
        if isinstance(c, type) and issubclass(c, altair.SchemaBase)
    )
    channel_to_name = {c: c._encoding_name for c in channel_objs}
    name_to_channel = {}
    for chan, name in channel_to_name.items():
        chans = name_to_channel.setdefault(name, {})
        key = "value" if chan.__name__.endswith("Value") else "field"
        chans[key] = chan

    # wrap hook shorthands
    for k, v in kwargs.items():
        if isinstance(v, AltairEncodingChannelHook):
            classes = name_to_channel[k]
            cls = classes["field"]
            obj = v.encoding_fields(cls)
            kwargs[k] = cls.from_dict(obj)

    return default_infer_encoding_types(args, kwargs, channels)


# original_chart_to_dict = altair.TopLevelMixin.to_dict


# def chart_to_dict(self, *args, **kwargs):
#     for spec, data in self._iterspecs():
#         if isinstance(data, DictumData):
#             query = spec._query()
#             result = data.project.execute(query)
#             spec.data = to_values(pd.DataFrame(result.data))
#     with warnings.catch_warnings():
#         warnings.simplefilter("ignore", UserWarning)
#         spec = original_chart_to_dict(self, *args, **kwargs)
#     return spec


original_field_channel_to_dict = altair.FieldChannelMixin.to_dict


def field_channel_to_dict(self, validate=True, ignore=(), context=None):
    shorthand = self._kwds.get("shorthand")
    if isinstance(shorthand, AltairEncodingChannelHook):
        encoding_fields = shorthand.encoding_fields(self.__class__)
        self.shorthand = altair.Undefined
        if self.type == altair.Undefined:
            self.type = encoding_fields["type"]
        self._kwds.update(
            update_nested(
                encoding_fields,
                {k: v for k, v in self._kwds.items() if v is not altair.Undefined},
            )
        )
    return original_field_channel_to_dict(
        self, validate=validate, ignore=ignore, context=context
    )


original_repr_mimebundle = altair.TopLevelMixin._repr_mimebundle_


def top_level_repr_mimebundle(self, *args, **kwargs):
    for spec, data in self._iterspecs():
        if isinstance(data, DictumData):
            query = spec._query()
            result = data.project.execute(query)
            spec.data = to_values(pd.DataFrame(result.data))
    return original_repr_mimebundle(self, *args, **kwargs)


def monkeypatch_altair():
    for cls in BaseMixin._registry:
        for altcls in cls._inject:
            if cls not in altcls.__bases__:
                altcls.__bases__ += (cls,)
    altair.TopLevelMixin._repr_mimebundle_ = top_level_repr_mimebundle
    altair.FieldChannelMixin.to_dict = field_channel_to_dict
    altair.utils.infer_encoding_types = infer_encoding_types


monkeypatch_altair()