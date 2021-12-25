class TableTransform:
    """While ScalarTransform operates only on a single expression, TableTransform
    is applied to a Computation as a whole.
    """


class TopTransform(TableTransform):
    """Only allowed in the limit clause. Adds an inner join."""


class TotalTransform(TableTransform):
    """For additive expressions: adds a post-calculation.
    For non-additive expressions (e.g. with COUNTD): adds a join, a total and a post-
        calculation.
    """


class PercentTransform(TableTransform):
    """Like total, but divides the value by the total."""
