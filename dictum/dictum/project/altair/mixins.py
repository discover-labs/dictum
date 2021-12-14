from altair import (
    FacetChart,
    FacetedUnitSpec,
    FieldName,
    NamedData,
    NormalizedFacetSpec,
    NormalizedSpec,
    RepeatSpec,
    TopLevelMixin,
    TopLevelUnitSpec,
    Undefined,
    UnitSpec,
)

from dictum.ql.transformer import compile_grouping
from dictum.schema import Query, QueryMetricRequest

dictum_data = NamedData("__dictum__")


class BaseMixin:
    _registry = set()
    _inject = ()

    def __init_subclass__(cls):
        if hasattr(cls, "_inject"):
            cls._registry.add(cls)


class ItemsMixin(BaseMixin):
    _inject = (TopLevelMixin, NormalizedSpec)
    _items = ["layer", "hconcat", "vconcat", "concat"]
    _specs = ["mark", "spec"]

    def _iteritems(self):
        """Iterate over the immediately-embedded specs."""
        for key in self._items:
            if hasattr(self, key):
                yield from getattr(self, key)

    def _iterspecs(self, data=None):
        """Iterate over all the embedded lowest-level specs."""
        for spec in self._specs:
            if hasattr(self, spec):
                yield self, self.data if (self.data is not Undefined) else data
                return
        for item in self._iteritems():
            yield from item._iterspecs(self.data if self.data != Undefined else data)


class UnitMixin(BaseMixin):
    _inject = (
        UnitSpec,
        TopLevelUnitSpec,
        FacetedUnitSpec,
        NormalizedFacetSpec,
        RepeatSpec,
        FacetChart,
    )
    _specmisc = ["facet", "repeat"]

    def _iterchannels(self):
        if hasattr(self, "spec"):
            yield from self.spec._iterchannels()
            if self.facet.column is not Undefined:
                yield self.facet.column
            if self.facet.row is not Undefined:
                yield self.facet.row
            return
        if self.encoding is not Undefined:
            for k in self.encoding._kwds:
                if (channel := getattr(self.encoding, k)) is not Undefined:
                    yield channel

    def _fields(self):
        for channel in self._iterchannels():
            yield channel.field

    def _query(self):
        metrics = []
        dimensions = []
        for channel in self._iterchannels():
            field = channel.field
            if isinstance(field, FieldName):
                field = field.to_dict()
            # skip normal fields or fields with shorthands
            if isinstance(field, str) and ":" in field:
                type_, field = field.split(":", maxsplit=1)
                if type_ == "metric":
                    request = QueryMetricRequest(metric=field)
                    channel.field = request.name
                    if request not in metrics:
                        metrics.append(request)
                    channel.field = FieldName(request.name)
                elif type_ == "dimension":
                    request = compile_grouping(field)
                    channel.field = request.name
                    if request not in dimensions:
                        dimensions.append(request)
                    channel.field = FieldName(request.name)
        return Query(metrics=metrics, dimensions=dimensions)
