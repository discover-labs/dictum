import inspect
import warnings
from typing import List

from altair import (
    Column,
    EncodingSortField,
    FacetChart,
    FacetedUnitSpec,
    FacetFieldDef,
    FieldName,
    LayerChart,
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
    renderers,
)
from altair.utils.core import update_nested
from altair.vegalite.v4.api import _EncodingMixin
from jsonschema.exceptions import ValidationError

from dictum.project.altair.data import DictumData
from dictum.project.altair.encoding import AltairEncodingChannelHook
from dictum.project.altair.locale import (
    cldr_locale_to_d3_number,
    cldr_locale_to_d3_time,
)
from dictum.ql.transformer import compile_dimension_request, compile_metric_request
from dictum.schema.query import Query, QueryMetricRequest


def is_channel_cls(obj):
    return (
        isinstance(obj, type)
        and obj is not channels.FieldChannelMixin
        and issubclass(obj, channels.FieldChannelMixin)
    )


original_chart_to_dict = TopLevelMixin.to_dict


def chart_to_dict(self, *args, **kwargs):
    """Ignore warnings about data not being a sublcass of altair.Data"""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        result = original_chart_to_dict(self, *args, **kwargs)
    return result


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
        if "sort" in kwargs and isinstance(kwargs["sort"], AltairEncodingChannelHook):
            kwargs["sort"] = EncodingSortField(
                field=kwargs["sort"].encoding_fields()["field"]
            )
        return original_channel_init(self, *args, **kwargs)

    return channel_init


original_encoding_sort_field_init = EncodingSortField.__init__


def encoding_sort_field_init(
    self, field=Undefined, op=Undefined, order=Undefined, **kwds
):
    if isinstance(field, AltairEncodingChannelHook):
        field = field.encoding_fields()["field"]
    return original_encoding_sort_field_init(
        self, field=field, op=op, order=order, *kwds
    )


original_repr_mimebundle = TopLevelMixin._repr_mimebundle_


def render_self(self):
    self = self.copy(deep=True)  # don't mutate the original
    currencies = set()
    currency = None
    model = None
    for unit, data in self._iterunits():
        if isinstance(data, DictumData):
            model = data.project.model
            query = unit._query()
            currencies |= model.get_currencies_for_query(query)
            result = data.get_values(query)
            if "repeat" in unit._kwds:
                unit.spec.data = result
            else:
                unit.data = result
    if len(currencies) == 1:
        currency = currencies.pop()
    if model is not None:
        renderers.set_embed_options(
            formatLocale=cldr_locale_to_d3_number(model.locale, currency),
            timeFormatLocale=cldr_locale_to_d3_time(model.locale),
        )
    return self


def rendered_dict(self):
    return self._render_self().to_dict()


def repr_mimebundle(self, *args, **kwargs):
    self = self._render_self()
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
    if "facet" in self._kwds:
        yield self, self.data if data is None else data
        return
    if "repeat" in self._kwds:
        yield self, self.spec.data if data is None else data
    for item in self._iteritems():
        yield from item._iterunits(self.data if self.data is not Undefined else data)


def iterchannels(self):
    if hasattr(self, "spec"):
        yield from self.spec._iterchannels()
        return
    if self.encoding is not Undefined:
        yield from self.encoding._iterattrs()
    for item in self._iteritems():
        yield from item._iterchannels()


def is_dictum_definition(req):
    if isinstance(req, FieldName):
        req = req.to_dict()
    return isinstance(req, str) and (
        req.startswith("metric:") or req.startswith("dimension:")
    )


def request_from_definition(defn: str):
    if isinstance(defn, FieldName):
        defn = defn.to_dict()
    type_, field = defn.split(":", maxsplit=1)
    if type_ == "metric":
        return compile_metric_request(field)
    if type_ == "dimension":
        return compile_dimension_request(field)
    raise ValueError(f"{defn} is not a valid Dictum definition.")


def request_from_field(field):
    if is_dictum_definition(field):
        return request_from_definition(field)


def requests_from_channel(channel):
    result = []
    if request := request_from_field(channel.field):
        result = [request]
        channel.field = request.name
    if "sort" in channel._kwds:
        if isinstance(channel.sort, dict):
            try:
                channel.sort = EncodingSortField.from_dict(channel.sort)
            except ValidationError:
                pass
        if isinstance(channel.sort, EncodingSortField) and is_dictum_definition(
            channel.sort.field
        ):
            request = request_from_field(channel.sort.field)
            result.append(request)
            channel.sort.field = request.name
    return result


def requests_from_list(items: List[str]):
    result = []
    for i, item in enumerate(items):
        if (req := request_from_field(item)) is not None:
            result.append(req)
            items[i] = req.name
    return result


def query(self):
    metrics = []
    dimensions = []

    def _add_requests(*reqs):
        for req in reqs:
            if isinstance(req, QueryMetricRequest):
                if req not in metrics:
                    metrics.append(req)
            elif req not in dimensions:
                dimensions.append(req)

    for channel in self._iterchannels():
        if isinstance(channel, channels.FieldChannelMixin):
            reqs = requests_from_channel(channel)
            _add_requests(*reqs)

    if "facet" in self._kwds:
        if isinstance(self.facet, FacetFieldDef):
            reqs = requests_from_channel(self.facet)
            _add_requests(*reqs)
        else:
            for attr in self.facet._iterattrs():
                if isinstance(attr, (Row, Column)):  # row/column
                    reqs = requests_from_channel(attr)
                    _add_requests(*reqs)

    if "repeat" in self._kwds:
        repeat = self["repeat"]
        if isinstance(repeat, list):
            reqs = requests_from_list(repeat)
            _add_requests(*reqs)
        else:
            for attr in repeat._iterattrs():
                reqs = requests_from_list(attr)
                _add_requests(*reqs)
    return Query(metrics=metrics, dimensions=dimensions)


units = (
    UnitSpec,
    TopLevelUnitSpec,
    FacetedUnitSpec,
    NormalizedFacetSpec,
    RepeatSpec,
    FacetChart,
    TopLevelRepeatSpec,
    LayerChart,
)


def monkeypatch_altair():
    TopLevelMixin.to_dict = chart_to_dict
    TopLevelMixin._render_self = render_self
    TopLevelMixin._rendered_dict = rendered_dict
    TopLevelMixin._repr_mimebundle_ = repr_mimebundle
    TopLevelMixin.repeat = repeat
    _EncodingMixin.encode = encode
    _EncodingMixin.facet = facet
    EncodingSortField.__init__ = encoding_sort_field_init
    for cls in channel_key_to_cls.values():
        cls.__init__ = build_channel_init(cls.__init__)
    inject(iterattrs_with_names, "_iterattrs_with_names", SchemaBase)
    inject(iterattrs, "_iterattrs", SchemaBase)
    inject(iteritems, "_iteritems", TopLevelMixin, NormalizedSpec)
    inject(iterunits, "_iterunits", TopLevelMixin, NormalizedSpec)
    inject(iterchannels, "_iterchannels", *units)
    inject(query, "_query", *units)