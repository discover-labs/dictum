from abc import ABC, abstractmethod
from typing import List

import pandas as pd
from lark import Token, Transformer

from nestor.store import Computation, RelationalQuery


class CallOwnerOp:
    def __get__(self, owner, ownertype=None):
        self._owner = owner
        return self

    def __set_name__(self, owner: "Transformer", name: str):
        self._owner = owner
        self._name = name

    def __call__(self, children: list):
        raise NotImplementedError


class PassChildrenToCompiler(CallOwnerOp):
    def __call__(self, children: list):
        return getattr(self._owner.compiler, self._name)(*children)


class PassTokenValueToCompiler(CallOwnerOp):
    def __call__(self, token: Token):
        return getattr(self._owner.compiler, self._name)(token.value)


def _get_whens_else(args: list):
    whens = [args[i : i + 2] for i in range(0, len(args), 2)]  # noqa: E203
    else_ = None if len(whens[-1]) == 2 else whens.pop(-1)[0]
    return whens, else_


class ExpressionTransformer(Transformer):
    def __init__(self, compiler: "Compiler", visit_tokens: bool = True) -> None:
        self.compiler = compiler
        super().__init__(visit_tokens=visit_tokens)

    FLOAT = PassTokenValueToCompiler()
    INTEGER = PassTokenValueToCompiler()
    STRING = PassTokenValueToCompiler()

    def TRUE(self, _):
        return self.compiler.TRUE()

    def FALSE(self, _):
        return self.compiler.FALSE()

    column = PassChildrenToCompiler()

    exp = PassChildrenToCompiler()
    neg = PassChildrenToCompiler()
    fdiv = PassChildrenToCompiler()
    div = PassChildrenToCompiler()
    mul = PassChildrenToCompiler()
    mod = PassChildrenToCompiler()
    add = PassChildrenToCompiler()
    sub = PassChildrenToCompiler()
    gt = PassChildrenToCompiler()
    gte = PassChildrenToCompiler()
    lt = PassChildrenToCompiler()
    lte = PassChildrenToCompiler()
    eq = PassChildrenToCompiler()
    neq = PassChildrenToCompiler()

    def IN(self, children: list):
        value, *values = children
        return self.compiler.IN(value, values)

    NOT = PassChildrenToCompiler()
    AND = PassChildrenToCompiler()
    OR = PassChildrenToCompiler()

    def case(self, children: list):
        whens, else_ = _get_whens_else(children)
        return self.compiler.case(whens, else_=else_)

    def expr(self, children: list):
        return children[0]

    def call(self, children: list):
        fn, *args = children
        return self.compiler.call(fn, args)


class Compiler(ABC):
    """Takes in a computation, returns an object that a connection will understand."""

    def __init__(self):
        self.transformer = ExpressionTransformer(self)

    # expression language elements

    @abstractmethod
    def FLOAT(self, value: str):
        """Float literal"""

    @abstractmethod
    def INTEGER(self, value: str):
        """Integer literal"""

    @abstractmethod
    def STRING(self, value: str):
        """String literal"""

    @abstractmethod
    def TRUE(self):
        """True boolean literal"""

    @abstractmethod
    def FALSE(self):
        """False boolean literal"""

    @abstractmethod
    def column(self, table: str, name: str):
        """Column reference.
        table is a dot-delimited sequence of identifiers
        name is the column name
        """

    def call(self, fn: str, args: list):
        """Function call. First element of children is function name, rest are
        the arguments. Calls the method on self.
        """
        call = getattr(self, fn)
        return call(args)

    @abstractmethod
    def exp(self, a, b):
        """Exponentiation — "power" operator, a to the power of b"""

    @abstractmethod
    def neg(self, value):
        """Unary number negation, e.g. -1"""

    @abstractmethod
    def div(self, a, b):
        """Normal division. Semantics depend on the underlying backend."""

    @abstractmethod
    def mul(sef, a, b):
        """Arithmetic multiplication"""

    @abstractmethod
    def mod(self, a, b):
        """Modulo, arithmetic remainder, e.g. 7 % 2 == 1"""

    @abstractmethod
    def add(self, a, b):
        """Arithmetic addition"""

    @abstractmethod
    def sub(self, a, b):
        """Arithmetic subtraction"""

    @abstractmethod
    def gt(self, a, b):
        """Greater than, a > b"""

    @abstractmethod
    def gte(self, a, b):
        """Greater than or equal, a >= b"""

    @abstractmethod
    def lt(self, a, b):
        """Less than, a < b"""

    @abstractmethod
    def lte(self, a, b):
        """Less than or equal, a <= b"""

    @abstractmethod
    def eq(self, a, b):
        """Equality, a equals b"""

    @abstractmethod
    def neq(self, a, b):
        """Non-equality, a not equals b"""

    @abstractmethod
    def IN(self, value, values):
        """Value is in a tuple of values"""

    @abstractmethod
    def NOT(self, value):
        """Boolean negation, NOT x"""

    @abstractmethod
    def AND(self, a, b):
        """Logical conjunction"""

    @abstractmethod
    def OR(self, a, b):
        """Logical disjunction"""

    @abstractmethod
    def case(self, whens, else_=None):
        """whens: tuples of (condition, value)
        else: else value (optional)
        """

    def IF(self, args: list):
        whens, else_ = _get_whens_else(args)
        return self.case(whens, else_=else_)

    # built-in functions
    # aggregate

    @abstractmethod
    def sum(self, args: list):
        """Aggregate sum"""

    @abstractmethod
    def avg(self, args: list):
        """Aggregate average"""

    @abstractmethod
    def min(self, args: list):
        """Aggregate minimum"""

    @abstractmethod
    def max(self, args: list):
        """Aggregate maximum"""

    @abstractmethod
    def count(self, args: list):
        """Aggregate count, with optional argument"""

    @abstractmethod
    def countd(self, args: list):
        """Aggregate distinct count"""

    # scalar functions

    @abstractmethod
    def abs(self, args: list):
        """Absolute numeric value"""

    @abstractmethod
    def floor(self, args: list):
        """Numeric floor"""

    @abstractmethod
    def ceil(self, args: list):
        """Numeric ceiling"""

    # dates

    @abstractmethod
    def datepart(self, args: list):
        """Part of a date as an integer. First arg is part as a string, e.g. 'month',
        second is date/datetime.
        """

    @abstractmethod
    def datetrunc(self, args: list):
        """Date truncated to a given part. Args same as datepart."""

    # compilation

    @abstractmethod
    def compile_query(self, query: RelationalQuery):
        """Compile a single relation query into connection query."""

    @abstractmethod
    def merge_queries(self, queries: List, merge_on: List[str]):
        """Merge a list of relational queries on the relevant level of detail."""

    @abstractmethod
    def calculate_metrics(self, merged):
        """Calculate"""

    def compile(self, computation: Computation):
        """Compile a computation returned by the store into an object that
        the connection will understand.
        """
        queries = [self.compile_query(q) for q in computation.queries]
        merged = self.merge_queries(queries, merge_on=computation.merge)
        return self.calculate_metrics(computation, merged)


class Connection(ABC):
    """User-facing. Gets connection details, knows about it's compiler. Compiles
    the incoming computation, executes on the client.
    """

    type: str
    compiler_cls = Compiler

    registry = {}

    def __init__(self):
        self.compiler = self.compiler_cls(self)

    def __init_subclass__(cls):
        cls.registry[cls.type] = cls

    def compute(self, computation: Computation) -> pd.DataFrame:
        return self.execute(self.compiler.compile(computation))

    @abstractmethod
    def execute(self, query) -> pd.DataFrame:
        """Execute a computation, return DataFrame"""
