from abc import ABC, abstractmethod
from enum import Enum

from lark import Transformer, Tree
from lark.exceptions import VisitError


class AbstractExprTransformer(Transformer, ABC):
    @abstractmethod
    def FLOAT(self, value: str):
        ...

    @abstractmethod
    def INTEGER(self, value: str):
        ...

    @abstractmethod
    def STRING(self, value: str):
        ...

    @abstractmethod
    def TRUE(self, _):
        ...

    @abstractmethod
    def FALSE(self, _):
        ...

    @abstractmethod
    def column(self, children: list):
        ...

    @abstractmethod
    def measure(self, children: list):
        ...

    @abstractmethod
    def dimension(self, children: list):
        ...

    @abstractmethod
    def call(self, children: list):
        ...

    @abstractmethod
    def exp(self, children: list):
        ...

    @abstractmethod
    def neg(self, children: list):
        ...

    @abstractmethod
    def fdiv(self, children: list):
        ...

    @abstractmethod
    def div(self, children: list):
        ...

    @abstractmethod
    def mul(self, children: list):
        ...

    @abstractmethod
    def mod(self, children: list):
        ...

    @abstractmethod
    def add(self, children: list):
        ...

    @abstractmethod
    def sub(self, children: list):
        ...

    @abstractmethod
    def gt(self, children: list):
        ...

    @abstractmethod
    def ge(self, children: list):
        ...

    @abstractmethod
    def lt(self, children: list):
        ...

    @abstractmethod
    def le(self, children: list):
        ...

    @abstractmethod
    def eq(self, children: list):
        ...

    @abstractmethod
    def ne(self, children: list):
        ...

    @abstractmethod
    def isnull(self, children: list):
        ...

    @abstractmethod
    def IN(self, children: list):
        ...

    @abstractmethod
    def NOT(self, children: list):
        ...

    @abstractmethod
    def AND(self, children: list):
        ...

    @abstractmethod
    def OR(self, children: list):
        ...

    @abstractmethod
    def case(self, children: list):
        ...

    @abstractmethod
    def expr(self, children: list):
        ...


class ExprKind(str, Enum):
    scalar = "scalar"
    aggregate = "aggregate"
    column = "column"


def scalar(self, _):
    return ExprKind.scalar


def _infer_kind(items: list):
    items = set(items)

    if len(items) == 1:
        return items.pop()

    if items == {ExprKind.column, ExprKind.scalar}:
        return ExprKind.column

    if items == {ExprKind.aggregate, ExprKind.scalar}:
        return ExprKind.aggregate

    if items & {ExprKind.aggregate, ExprKind.column}:
        raise ValueError("Mixing aggregates and non-aggregates in expression")

    raise ValueError(f"Unknown combination of kinds: {items}")


def infer_kind(self, children: list):
    return _infer_kind(children)


aggregate_functions = {
    "sum",
    "count",
    "countd",
    "min",
    "max",
    "avg",
}


class ExprKindTransformer(AbstractExprTransformer):
    """Checks that the expression is valid, namely that it's not mixing
    aggregate and non-aggregate parts, e.g.
        column + sum(another_column) isn't valid

    parts of expressions can be
        - scalar (constants)
        - aggregate (result of aggregate function)
        - column (a column reference or a scalar operation on it)

    things inside aggregate function calls must be scalar or column
    operations with aggregates must be scalar or aggregate

    scalar + scalar gives scalar
    scalar + column gives column

    agg(scalar) gives aggregate
    agg(column) gives aggregate
    agg(aggregate) is invalid

    aggregate + scalar gives aggregate
    aggregate + column is invalid
    """

    FLOAT = scalar
    INTEGER = scalar
    STRING = scalar
    TRUE = scalar
    FALSE = scalar

    def column(self, _):
        return ExprKind.column

    def measure(self, _):
        return ExprKind.aggregate

    def dimension(self, _):
        return ExprKind.column

    def call(self, children: list):
        fn, *args = children
        if fn in aggregate_functions:
            if args and args[0] == ExprKind.aggregate:
                raise ValueError(
                    f"Aggregate function {fn} expects a scalar "
                    "or a column expression argument"
                )
            return ExprKind.aggregate
        return _infer_kind(args)

    exp = infer_kind
    neg = infer_kind
    fdiv = infer_kind
    div = infer_kind
    mul = infer_kind
    mod = infer_kind
    add = infer_kind
    sub = infer_kind
    gt = infer_kind
    ge = infer_kind
    lt = infer_kind
    le = infer_kind
    eq = infer_kind
    ne = infer_kind
    eq = infer_kind
    ne = infer_kind
    isnull = infer_kind
    IN = infer_kind
    NOT = infer_kind
    AND = infer_kind
    OR = infer_kind

    def case(self, children: list):
        return _infer_kind(children)

    def expr(self, children: list):
        return children[0]


expr_kind_transformer = ExprKindTransformer()


def get_expr_kind(expr: Tree) -> ExprKind:
    try:
        return expr_kind_transformer.transform(expr)
    except VisitError as e:
        raise ValueError(f"error in expression {e.obj.data}: {e.orig_exc}")


class TotalFunctionExprTransformer(Transformer):
    """For aggregate expressions we need to figure out which function (if any) to use
    for calculating its totals.

    We know for sure which function to use if an aggregate is just a bare function:
        sum -> sum
        count -> sum
        max -> max
        min -> min
    For all other cases, e.g. countd, sum(..) + 1 or sum(..) / sum(..), return None
    (no function), so that the system can calculate the total some other way (subquery).

    Mainly to be used in total and percent transforms.
    """

    def expr(self, children: list):
        return children[0]

    def call(self, children: list):
        fn, *_ = children
        if fn == "count":
            return "sum"
        if fn in {"sum", "min", "max"}:
            return fn
        # TODO: maybe there are more cases where the function is known?
        return None  # unknown

    def __default__(self, *_):
        return None


total_function_expr_transformer = TotalFunctionExprTransformer()


def get_expr_total_function(expr: Tree) -> str:
    return total_function_expr_transformer.transform(expr)
