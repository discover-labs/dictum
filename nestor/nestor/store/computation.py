from dataclasses import dataclass
from typing import Dict, List, Tuple

import lark


class Op:
    pass


class AnchorTableOp(Op):
    """Select data from the anchor table. Always the first step.
    Any select is
    """
    id: str


class JoinOp:
    table: str
    on: Tuple[str, str]


class FilterOp:
    condition: lark.Tree


class CalculateOp:
    calculate: Dict[str, lark.Tree]


class Agg:
    pass


class AggregateOp:
    groupby: List[str]
    aggregate: List[Agg]


@dataclass
class Tables:
    id: str
    tables: List["Tables"]  # a tree of joins


@dataclass
class Computation:
    """...
    - Tables and columns
    - How to join them
    - How to aggregate them

    - Which tables to I select from?
    - How do I join the tables?
    - Which computations do I perform before aggregating
        - Dimensions
    - How do I compute the aggregates (measures)?
    """
