from lark import Transformer

from nestor.store import Computation


class CallOwnerBinaryOp:
    def __get__(self, owner, ownertype=None):
        self._owner = owner
        return self

    def __set_name__(self, owner: "Transformer", name: str):
        self._owner = owner
        self._name = name

    def __call__(self, children: list):
        return getattr(self._owner.compiler, self._name)(*children)


class ExpressionTransformer(Transformer):
    def __init__(self, compiler: "Compiler", visit_tokens: bool = True) -> None:
        self.compiler = compiler
        super().__init__(visit_tokens=visit_tokens)

    def expr(self, children: list):
        return children[0]

    def call(self, children: list):
        fn, *args = children
        call = getattr(self.compiler, fn)
        return call(args)

    def column(self, children: list):
        identity, column = children
        return self.compiler.column(identity, column)

    add = CallOwnerBinaryOp()
    sub = CallOwnerBinaryOp()
    mul = CallOwnerBinaryOp()
    div = CallOwnerBinaryOp()
    mod = CallOwnerBinaryOp()
    eq = CallOwnerBinaryOp()
    neq = CallOwnerBinaryOp()
    gt = CallOwnerBinaryOp()
    gte = CallOwnerBinaryOp()
    lt = CallOwnerBinaryOp()
    lte = CallOwnerBinaryOp()


class Compiler:
    """Takes in a computation, returns an object that a connection will understand."""

    def __init__(self):
        self.transformer = ExpressionTransformer(self)

    def call(self, children: list):
        fn, *args = children
        call = getattr(self, fn)
        return call(args)

    def column(self, table_identity: str, name: str):
        raise NotImplementedError

    def sum(self, args: list):
        raise NotImplementedError

    def avg(self, args: list):
        raise NotImplementedError

    def min(self, args: list):
        raise NotImplementedError

    def max(self, args: list):
        raise NotImplementedError

    def distinct(self, args: list):
        raise NotImplementedError

    def floor(self, args: list):
        raise NotImplementedError

    def ceil(self, args: list):
        raise NotImplementedError

    def add(self, a, b):
        raise NotImplementedError

    def sub(self, a, b):
        raise NotImplementedError

    def mul(self, a, b):
        raise NotImplementedError

    def div(self, a, b):
        raise NotImplementedError

    def paren(self, children: list):
        raise NotImplementedError

    def compile(self, computation: Computation):
        raise NotImplementedError


class Connection:
    """User-facing. Gets connection details, knows about it's compiler. Compiles
    the incoming computation, executes on the client.
    """

    type: str

    registry = {}
    compiler = Compiler()

    def __init_subclass__(cls):
        cls.registry[cls.type] = cls

    def execute(self, computation: Computation):
        raise NotImplementedError
