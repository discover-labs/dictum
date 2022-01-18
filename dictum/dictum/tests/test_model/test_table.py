import pytest

from dictum.model import Model
from dictum.model.table import RelatedTable, Table


def test_table_find_all_paths_chinook(chinook: Model):
    paths = list(chinook.tables["invoice_items"].find_all_paths())
    assert len(paths) == 8


def test_table_allowed_join_paths(chinook: Model):
    table = chinook.tables["invoice_items"]
    assert len(table.allowed_join_paths) == 8


def test_table_allowed_dimensions(chinook: Model):
    table = chinook.tables["invoice_items"]
    assert "artist" in table.allowed_dimensions
    assert "customer_country" in table.allowed_dimensions


def test_table_allowed_dimensions_union(chinook: Model):
    assert "country" not in chinook.tables.get("invoice_items").allowed_dimensions
    assert "country" in chinook.tables.get("customers").allowed_dimensions


@pytest.fixture(scope="module")
def t1() -> Table:
    """Table graph representing (hopefully) all possible table relatioship cases
    - Self join
    - Related self join
    - Directly related table
    - Relationship cycle
    - Duplicate join path

    ┌┐          ┌┐    ┌─────┐
    ▼┘          ▼┘    ▼     │
    t1 ─► t2 ─► t3 ─► t4 ─► t5
    │                       ▲
    └► t6 ──────────────────┘

    Returns: t1
    """

    def create_rel(parent, table):
        return RelatedTable.create(
            table=table,
            alias=table.id,
            foreign_key=f"{table.id}_id",
            related_key="id",
            parent=parent,
        )

    t1 = Table(id="t1", source="test")
    t2 = Table(id="t2", source="test")
    t3 = Table(id="t3", source="test")
    t4 = Table(id="t4", source="test")
    t5 = Table(id="t5", source="test")
    t6 = Table(id="t6", source="test")
    t1.related["t1"] = create_rel(t1, t1)
    t1.related["t2"] = create_rel(t1, t2)
    t1.related["t6"] = create_rel(t1, t6)
    t2.related["t3"] = create_rel(t2, t3)
    t3.related["t3"] = create_rel(t3, t3)
    t3.related["t4"] = create_rel(t3, t4)
    t4.related["t5"] = create_rel(t4, t5)
    t5.related["t4"] = create_rel(t5, t4)
    t6.related["t5"] = create_rel(t6, t5)
    return t1


def test_find_all_paths(t1: Table):
    assert [p for _, p in t1.find_all_paths()] == [
        ["t2"],
        ["t2", "t3"],
        ["t2", "t3", "t4"],
        ["t2", "t3", "t4", "t5"],
        ["t6"],
        ["t6", "t5"],
        ["t6", "t5", "t4"],
    ]


def test_allowed_join_paths(t1: Table):
    paths = {t.id: path for t, path in t1.allowed_join_paths.items()}
    assert paths == {"t2": ["t2"], "t3": ["t2", "t3"], "t6": ["t6"], "t1": ["t1"]}
