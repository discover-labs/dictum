from typing import List, Optional

from lark import Transformer, Tree

from dictum import schema
from dictum.data_model.expr import parse_expr
from dictum.data_model.transforms.base import BaseTransform


class TransformTransformer(Transformer):
    def __init__(self, arg, args: dict, visit_tokens: bool = True) -> None:
        self._arg = arg
        self._args = args
        super().__init__(visit_tokens=visit_tokens)

    def column(self, children: list):
        return self._args[children[0]]

    def ARG(self, _):
        return self._arg

    def expr(self, children):
        return children[0]


transforms = {}


class ScalarTransform(BaseTransform):
    """A scalar transform. Transforms a given ColumnCalculation. Can change it's expr,
    name and type.
    """

    id: str
    name: str
    description: Optional[str] = None
    return_type: Optional[schema.Type] = None

    def __init_subclass__(cls):
        if hasattr(cls, "id") and cls.id is not None:
            transforms[cls.id] = cls


class LiteralTransform(ScalarTransform):
    """A kind of ScalarTransform that's defined with a literal expression.
    @ token gets replaced with expr of the argument.
    """

    expr: str
    args: List[str] = []

    @property
    def _expr(self) -> Tree:
        return parse_expr(self.expr)

    def transform_expr(self, expr: Tree):
        kwargs = dict(zip(self.args, self._args))
        transformer = TransformTransformer(expr, kwargs)
        return transformer.transform(self._expr)


class InvertTransform(LiteralTransform):
    id = "invert"
    return_type = "bool"
    expr = "not (@)"


class BooleanTransform(LiteralTransform):
    args = ["value"]
    return_type = "bool"
    op: str

    def __init_subclass__(cls):
        cls.id = cls.__name__[:2].lower()
        cls.name = cls.op
        cls.expr = f"(@) {cls.op} value"
        super().__init_subclass__()


class EqTransform(BooleanTransform):
    op = "="


class NeTransform(BooleanTransform):
    op = "!="


class GtTransform(BooleanTransform):
    op = ">"


class GeTransform(BooleanTransform):
    op = ">="


class LtTransform(BooleanTransform):
    op = "<"


class LeTransform(BooleanTransform):
    op = "<="


class IsNullTransform(LiteralTransform):
    id = "isnull"
    name = "IS NULL"
    return_type = "bool"
    expr = "@ is null"


class IsNotNullTransform(LiteralTransform):
    id = "isnotnull"
    name = "IS NOT NULL"
    return_type = "bool"
    expr = "@ is not null"


class InRangeTransform(LiteralTransform):
    id = "inrange"
    name = "in range"
    return_type = "bool"
    args = ["min", "max"]
    expr = "@ >= min and @ <= max"


class IsInTransform(ScalarTransform):
    id = "isin"
    name = "IN"
    return_type = "bool"

    def transform_expr(self, expr: Tree) -> Tree:
        return Tree("IN", [expr, *self._args])


class LastTransform(LiteralTransform):
    id = "last"
    name = "last"
    return_type = "bool"
    args = ["n", "part"]
    expr = "datediff(part, @, now()) <= n"

    def __init__(self, n: int, period: str):
        super().__init__(n, period)


class StepTransform(LiteralTransform):
    id = "step"
    name = "step"
    return_type = "int"
    args = ["size"]
    expr = "@ // size * size"


class DatepartTransform(LiteralTransform):
    id = "datepart"
    name = "date part"
    args = ["part"]
    return_type = "int"
    expr = "datepart(part, @)"

    def __init__(self, part: str):
        super().__init__(part)


class ShortDatepartTransform(DatepartTransform):
    id = None

    def __init__(self):
        super().__init__(self.id)


class YearTransform(ShortDatepartTransform):
    id = "year"
    name = "Year"


class QuarterTransform(ShortDatepartTransform):
    id = "quarter"
    name = "Quarter"


class MonthTransform(ShortDatepartTransform):
    id = "month"
    name = "Month"


class WeekTransform(ShortDatepartTransform):
    id = "week"
    name = "Week"


class DayTransform(ShortDatepartTransform):
    id = "day"
    name = "Day"


class HourTransform(ShortDatepartTransform):
    id = "hour"
    name = "Hour"


class MinuteTransform(ShortDatepartTransform):
    id = "minute"
    name = "Minute"


class SecondTransform(ShortDatepartTransform):
    id = "second"
    name = "Second"


date_skeletons = {
    "year": "y",
    "quarter": "yQQQ",
    "month": "yMMM",
    "week": "yw",
    "day": "yMd",
}


class DatetruncTransform(ScalarTransform):
    id = "datetrunc"
    name = "Truncate a date"
    return_type = "datetime"

    def __init__(self, period: str):
        super().__init__(period)

    def get_format(self, type_: str) -> schema.FormatConfig:
        part = self._args[0]
        if part in date_skeletons:
            return schema.FormatConfig(kind="date", skeleton=date_skeletons[part])
        return schema.FormatConfig(kind="datetime")

    def transform_expr(self, expr: Tree):
        return Tree("call", ["datetrunc", *self._args, expr])


class DateTransform(DatetruncTransform):
    id = "date"
    name = "Truncate a datetime to a date"

    def __init__(self):
        super().__init__("day")
