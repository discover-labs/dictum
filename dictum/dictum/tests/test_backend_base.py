from unittest import mock

from dictum.backends.base import ExpressionTransformer


def test_compiler_case():
    compiler = mock.MagicMock()
    transformer = ExpressionTransformer(compiler)
    transformer.case([1, 2, 3, 4])
    compiler.case.assert_called_once_with([[1, 2], [3, 4]], else_=None)

    transformer.case([1, 2, 3, 4, 5])
    compiler.case.assert_called_with([[1, 2], [3, 4]], else_=5)
