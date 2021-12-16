import inspect
from typing import List

from altair import (
    Column,
    FacetChart,
    FacetedUnitSpec,
    FacetFieldDef,
    FieldName,
    NormalizedFacetSpec,
    NormalizedSpec,
    RepeatSpec,
    Row,
    SchemaBase,
    TopLevelMixin,
    TopLevelRepeatSpec,
    TopLevelUnitSpec,
    Undefined,
    UnitSpec,
    channels,
)
from altair.utils.core import update_nested
from altair.vegalite.v4.api import _EncodingMixin

from dictum.project.altair.data import DictumData
from dictum.project.altair.encoding import AltairEncodingChannelHook
from dictum.ql.transformer import compile_grouping
from dictum.schema.query import Query, QueryMetricRequest


def is_channel_cls(obj):
    return (
        isinstance(obj, type)
        and obj is not channels.FieldChannelMixin
        and issubclass(obj, channels.FieldChannelMixin)
    )


original_encode = _EncodingMixin.encode

channel_key_to_cls = {
    name.lower(): cls for name, cls in inspect.getmembers(channels, is_channel_cls)
}


def encode(self, *args, **kwargs):
    for name, obj in kwargs.items():
        if isinstance(obj, AltairEncodingChannelHook):
            # channel __init__ will handle resolution
            kwargs[name] = channel_key_to_cls[name](obj)
    return original_encode(self, *args, **kwargs)


def _resolve_repeat_objs(objs: list) -> list:
    if objs is Undefined:
        return objs
    result = []
    for obj in objs:
        if isinstance(obj, AltairEncodingChannelHook):
            result.append(obj.encoding_fields()["field"])
        else:
            result.append(obj)
    return result


original_repeat = TopLevelMixin.repeat


def repeat(
    self,
    repeat=Undefined,
    row=Undefined,
    column=Undefined,
    layer=Undefined,
    columns=Undefined,
    **kwargs,
):
    repeat = _resolve_repeat_objs(repeat)
    row = _resolve_repeat_objs(row)
    column = _resolve_repeat_objs(column)
    layer = _resolve_repeat_objs(layer)
    return original_repeat(
        self,
        repeat=repeat,
        row=row,
        column=column,
        layer=layer,
        columns=columns,
        **kwargs,
    )


original_facet = _EncodingMixin.facet


def _resolve_facet_def(obj, cls):
    if obj is Undefined:
        return obj
    if isinstance(obj, AltairEncodingChannelHook):
        fields = obj.encoding_fields(cls)  # doesn't really matter, we want the header
        return cls.from_dict(fields)


def facet(
    self,
    facet=Undefined,
    row=Undefined,
    column=Undefined,
    data=Undefined,
    columns=Undefined,
    **kwargs,
):
    facet = _resolve_facet_def(facet, FacetFieldDef)
    row = _resolve_facet_def(row, Row)
    column = _resolve_facet_def(column, Column)
    return original_facet(
        self, facet=facet, row=row, column=column, data=data, columns=columns, **kwargs
    )


def _update_nested(a, b):
    """Like Altair's update_nested, but convert everything to dicts beforehand."""
    for k, v in b.items():
        if isinstance(v, SchemaBase):
            b[k] = v.to_dict()
    return update_nested(a, b)


def build_channel_init(original_channel_init):
    def channel_init(self, *args, **kwargs):
        if args:
            shorthand, *args = args
            if isinstance(shorthand, AltairEncodingChannelHook):
                fields = shorthand.encoding_fields(self.__class__)
                kwargs = _update_nested(fields, kwargs)
            else:
                kwargs["shorthand"] = shorthand
        return original_channel_init(self, *args, **kwargs)

    return channel_init


original_repr_mimebundle = TopLevelMixin._repr_mimebundle_


def repr_mimebundle(self, *args, **kwargs):
    for unit, data in self._iterunits():
        if isinstance(data, DictumData):
            query = unit._query()
            data = data.get_values(query)
            if "spec" in unit._kwds:
                unit.spec.data = data
            else:
                unit.data = data
    return original_repr_mimebundle(self, *args, **kwargs)


def inject(method: callable, name: str, *classes):
    """Add a method into multiple classes"""
    for cls in classes:
        setattr(cls, name, method)


def iterattrs_with_names(self):
    yield from (
        (name, attr) for name, attr in self._kwds.items() if attr is not Undefined
    )


def iterattrs(self):
    """Iterate over non-undefined attributes"""
    yield from (attr for _, attr in iterattrs_with_names(self))


_items = ["layer", "hconcat", "vconcat", "concat"]


def iteritems(self):
    """Iterate over the immediately-embedded specs."""
    for key in _items:
        if hasattr(self, key):
            yield from getattr(self, key)


def iterunits(self, data=None):
    """Iterate over all the embedded lowest-level specs, returning a tuple of spec, data"""
    if "mark" in self._kwds:
        yield self, self.data if data is None else data
        return
    if "spec" in self._kwds:
        yield self, self.data if data is None else data
        return
    for item in self._iteritems():
        yield from item._iterunits(self.data if self.data is not Undefined else data)


def iterchannels(self):
    if hasattr(self, "spec"):
        yield from self.spec._iterchannels()
        return
    if self.encoding is not Undefined:
        yield from self.encoding._iterattrs()


def is_dictum_definition(req):
    return isinstance(req, str) and (
        req.startswith("metric:") or req.startswith("dimension:")
    )


def request_from_definition(defn: str):
    type_, field = defn.split(":", maxsplit=1)
    if type_ == "metric":
        return QueryMetricRequest(metric=field)
    if type_ == "dimension":
        return compile_grouping(field)
    raise ValueError(f"{defn} is not a valid Dictum definition.")


def request_from_field(field):
    if isinstance(field, FieldName):
        field = field.to_dict()  # to str, really
    if is_dictum_definition(field):
        return request_from_definition(field)


def requests_from_list(items: List[str]):
    requests = []
    names = []
    for item in items:
        if (req := request_from_field(item)) is not None:
            requests.append(req)
            names.append(req.name)
        else:
            names.append(item)
    return requests, names


def query(self):
    metrics = []
    dimensions = []

    def _add_request(req):
        if isinstance(req, QueryMetricRequest):
            if req not in metrics:
                metrics.append(req)
        elif req not in dimensions:
            dimensions.append(req)

    for channel in self._iterchannels():
        if (
            isinstance(channel, channels.FieldChannelMixin)
            and (req := request_from_field(channel.field)) is not None
        ):
            _add_request(req)
            channel.field = req.name

    if "facet" in self._kwds:
        for name, attr in self["facet"]._iterattrs_with_names():
            if isinstance(attr, FacetFieldDef):  # facet attribute
                if (req := request_from_field(attr.field)) is not None:
                    _add_request(req)
            elif isinstance(attr, (Row, Column)):  # row/column
                req = request_from_field(attr.field)
                attr.field = req.name
                _add_request(req)

    if "repeat" in self._kwds:
        repeat = self["repeat"]
        if isinstance(repeat, list):
            requests, names = requests_from_list(repeat)
            self["repeat"]["name"] = names
            for req in requests:
                _add_request(req)
        else:
            for name, attr in repeat._iterattrs_with_names():
                requests, names = requests_from_list(attr)
                self["repeat"][name] = names
                for req in requests:
                    _add_request(req)
    return Query(metrics=metrics, dimensions=dimensions)


units = (
    UnitSpec,
    TopLevelUnitSpec,
    FacetedUnitSpec,
    NormalizedFacetSpec,
    RepeatSpec,
    FacetChart,
    TopLevelRepeatSpec,
)


def monkeypatch_altair():
    TopLevelMixin._repr_mimebundle_ = repr_mimebundle
    TopLevelMixin.repeat = repeat
    _EncodingMixin.encode = encode
    _EncodingMixin.facet = facet
    for cls in channel_key_to_cls.values():
        cls.__init__ = build_channel_init(cls.__init__)
    inject(iterattrs_with_names, "_iterattrs_with_names", SchemaBase)
    inject(iterattrs, "_iterattrs", SchemaBase)
    inject(iteritems, "_iteritems", TopLevelMixin, NormalizedSpec)
    inject(iterunits, "_iterunits", TopLevelMixin, NormalizedSpec)
    inject(iterchannels, "_iterchannels", *units)
    inject(query, "_query", *units)
