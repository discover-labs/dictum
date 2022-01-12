from threading import Event, Thread
from typing import List

from pandas import DataFrame, concat

from dictum import engine


class Backend:
    def execute(self, query):
        """Execute a query"""

    def compile(self, query: engine.RelationalQuery):
        """Compile a RelationalQuery into a backend-specific query"""

    def calculate(self, query, columns: List[engine.Column]):
        """Calculate a list of columns based on an input query"""

    def inner_join(self, base, query):
        """Inject a query into base as an inner join on all query columns. Match by
        column names.
        """


class Operator(Thread):
    def __init__(self, backend: Backend, dependencies: List["Operator"]):
        self.backend = backend
        self.dependencies = dependencies
        self.result = None
        self.ready = Event()

    def start(self):
        for dependency in self.dependencies:
            dependency.start()
        return super().start()

    def run(self):
        self.result = self.execute(self.backend)
        self.ready.set()

    def execute(self, backend: Backend):
        """Actual operator logic. Execute any upstreams."""
        raise NotImplementedError

    def get_result(self):
        with self.ready:
            return self.result


class QueryOperator(Operator):
    def __init__(self, backend: Backend, query: engine.RelationalQuery):
        self.query = query
        super().__init__(backend, [])

    def execute(self, backend: Backend):
        return backend.compile(self.query)


class InnerJoinOperator(Operator):
    def __init__(self, backend: Backend, base: Operator, query: Operator):
        self.base = base
        self.query = query
        super().__init__(backend, [base, query])

    def execute(self, backend: Backend):
        return backend.inner_join(
            self.base.get_result(backend), self.query.get_result(backend)
        )


class MergeOperator(Operator):
    def __init__(self, queries: List[Operator]):
        self.queries = queries

    def execute(self, backend: Backend):
        results = []
        for query in self.queries:
            result = query.get_result(backend)
            if not isinstance(result, DataFrame):
                result = backend.execute(result)
            results.append(result)
        return concat(results, axis=1)


class CalculateOperator(Operator):
    def __init__(self, input: Operator, columns: List[engine.Column]):
        self.input = input
        self.columns = columns

    def execute(self, backend: Backend):
        result = self.input.get_result(backend)
        if isinstance(result, DataFrame):
            ...  # calculate with pandas and return
        return backend.calculate(result, self.columns)


class MaterializeOperator(Operator):
    def __init__(self, inputs: List[Operator]):
        self.inputs = inputs

    def execute(self, backend: Backend) -> List[DataFrame]:
        results = []
        for input in self.inputs:
            result = input.get_result(backend)
            if not isinstance(result, DataFrame):
                result = backend.execute(result)
            results.append(result)
        return results


class FinalizeOperator(MaterializeOperator):
    def __init__(self, inputs: List[Operator], columns: List[engine.Column]):
        super().__init__(inputs)
        self.columns = columns

    def execute(self, backend: Backend) -> List[DataFrame]:
        results = super().execute(backend)
        return concat(results, axis=1)  # TODO: typecast
