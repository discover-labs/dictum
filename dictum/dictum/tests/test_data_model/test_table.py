import pytest

from dictum.data_model import DataModel
from dictum.data_model.table import RelatedTable, Table


def test_table_find_all_paths_chinook(chinook: DataModel):
    paths = list(chinook.tables["invoice_items"].find_all_paths())
    assert len(paths) == 8


def test_table_allowed_join_paths(chinook: DataModel):
    table = chinook.tables["invoice_items"]
    assert len(table.allowed_join_paths) == 8


def test_table_allowed_dimensions(chinook: DataModel):
    table = chinook.tables["invoice_items"]
    assert "artist" in table.allowed_dimensions
    assert "customer_country" in table.allowed_dimensions


def test_table_allowed_dimensions_union(chinook: DataModel):
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
    t1 = Table(id="t1", source="test")
    t1rel = RelatedTable(table=t1, alias="t1", foreign_key="t1_id", related_key="id")
    t2 = Table(id="t2", source="test")
    t2rel = RelatedTable(table=t2, alias="t2", foreign_key="t2_id", related_key="id")
    t3 = Table(id="t3", source="test")
    t3rel = RelatedTable(table=t3, alias="t3", foreign_key="t3_id", related_key="id")
    t4 = Table(id="t4", source="test")
    t4rel = RelatedTable(table=t4, alias="t4", foreign_key="t4_id", related_key="id")
    t5 = Table(id="t5", source="test")
    t5rel = RelatedTable(table=t5, alias="t5", foreign_key="t5_id", related_key="id")
    t6 = Table(id="t6", source="test")
    t6rel = RelatedTable(table=t6, alias="t6", foreign_key="t6_id", related_key="id")
    t1.related["t1"] = t1rel
    t1.related["t2"] = t2rel
    t1.related["t6"] = t6rel
    t2.related["t3"] = t3rel
    t3.related["t3"] = t3rel
    t3.related["t4"] = t4rel
    t4.related["t5"] = t5rel
    t5.related["t4"] = t4rel
    t6.related["t5"] = t5rel
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
