from dataclasses import dataclass, field
from functools import cached_property
from typing import Dict, List, Optional, Tuple

from lark import Transformer, Tree

import nestor.store
from nestor.store import schema
from nestor.store.schema.types import CalculationType


class ColumnReferenceTransformer(Transformer):
    """Replaces a list of tables in a column reference with a '.'-delimited string."""

    def __init__(self, base_path: List[str], visit_tokens: bool = True) -> None:
        self._base = base_path
        super().__init__(visit_tokens=visit_tokens)

    def column(self, children):
        *tables, column = children
        return Tree("column", [".".join([*self._base, *tables]), column])


@dataclass
class Calculation:
    """Parent class for measures and dimensions."""

    id: str
    name: str
    description: Optional[str]
    expr: Tree
    str_expr: str
    format: Optional[schema.CalculationFormat]

    @cached_property
    def join_paths(self) -> List[List[str]]:
        result = []
        for column in self.expr.find_data("column"):
            *tables, _ = column.children
            if tables:
                result.append(list(tables))
        return result

    def prepare_expr(self, base_path: List[str]) -> Tree:
        t = ColumnReferenceTransformer(base_path)
        return t.transform(self.expr)

    def prepare_range_expr(self, base_path: List[str]) -> Tuple[Tree, Tree]:
        return (
            Tree("call", ["min", self.prepare_expr(base_path)]),
            Tree("call", ["max", self.prepare_expr(base_path)]),
        )

    @cached_property
    def metadata(self) -> schema.CalculationMetadata:
        return schema.CalculationMetadata(
            name=self.name,
            format=self.format,
            kind="dimension" if isinstance(self, Dimension) else "measure",
            type=getattr(self, "type", None),
        )

    def __str__(self):
        return f"{self.__class__.__name__}({self.id})"

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return self.id == other.id


@dataclass(eq=False, repr=False)
class TableCalculation(Calculation):
    table: "nestor.store.Table"

    @cached_property
    def joins(self) -> List["nestor.store.Join"]:
        result = []
        for ref in self.expr.find_data("column"):
            *tables, _ = ref.children
            if len(tables) > 0:
                related = self.table.related.get(tables[0])
                join = nestor.store.Join(
                    foreign_key=related.foreign_key,
                    related_key=related.table.primary_key,
                    alias=tables[0],
                    to=nestor.store.RelationalQuery(table=related.table),
                )
                join.to.add_path(tables[1:])
                result.append(join)
        return result


@dataclass(eq=False, repr=False)
class Dimension(TableCalculation):
    # not really a default, schema prevents that
    type: CalculationType = CalculationType.continuous

    @cached_property
    def joins(self) -> List["nestor.store.Join"]:
        joins = []
        for ref in self.expr.find_data("measure"):
            # figure out the subquery — group the measure by self.table.primary_key
            measure_id = ref.children[0]
            source_table = self.table.measure_backlinks[measure_id]
            query = nestor.store.RelationalQuery(
                table=source_table,
                subquery=True,
            )
            query.add_measure(measure_id)
            path = [p.alias for p in source_table.allowed_join_paths.get(self.table.id)]
            query.add_path(path)
            query.groupby[self.table.primary_key] = Tree(
                "expr",
                [
                    Tree(
                        "column",
                        [
                            ".".join([source_table.id, *path]),
                            self.table.primary_key,
                        ],
                    )
                ],
            )

            # add the join
            join = nestor.store.Join(
                foreign_key=self.table.primary_key,
                related_key=self.table.primary_key,
                alias=measure_id,
                to=query,
            )
            joins.append(join)
        return [*super().joins, *joins]


@dataclass(repr=False)
class Measure(TableCalculation):
    @cached_property
    def dimensions(self):
        return list(self.table.allowed_dimensions.values())

    def metric(self, key: bool) -> "Metric":
        return Metric(
            self.id,
            name=self.name,
            description=self.description,
            expr=Tree("expr", [Tree("measure", [self.id])]),
            str_expr=self.str_expr,
            format=self.format,
            measures=[self],
            key=key,
        )


@dataclass(repr=False)
class Metric(Calculation):
    measures: List[Measure] = field(default_factory=lambda: [])
    key: bool = False

    @cached_property
    def dimensions(self) -> Dict[str, Dimension]:
        return sorted(
            set.intersection(*(set(m.dimensions) for m in self.measures)),
            key=lambda x: x.name,
        )
