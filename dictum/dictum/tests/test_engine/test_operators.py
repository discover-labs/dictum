from dictum.engine.operators import Operator


class DummyOperator(Operator):
    def __init__(self, input):
        self.input = input
        super().__init__()

    def execute(self, backend):
        if not isinstance(self.input, Operator):
            return self.input
        return self.input.get_result(backend)


def test_run_once():
    op1 = DummyOperator(42)
    op2 = DummyOperator(op1)
    op3 = DummyOperator(op2)
    assert op3.get_result(None) == 42
    assert op3.get_result(None) == 42  # won't call Thread.start() twice
