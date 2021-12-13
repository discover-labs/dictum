import altair as alt

from dictum.project.altair import monkeypatch_altair

monkeypatch_altair()


def test_iterspecs():
    ch = alt.Chart("#").mark_bar()

    assert len(list(ch._iterspecs())) == 1
    assert len(list((ch + ch)._iterspecs())) == 2
    assert len(list((ch | ch)._iterspecs())) == 2
    assert len(list((ch & ch)._iterspecs())) == 2
    assert len(list((ch | ch | ch)._iterspecs())) == 3
    assert len(list((ch & ch & ch)._iterspecs())) == 3
    assert len(list((ch | ch & ch)._iterspecs())) == 3
    assert len(list((ch & ch | ch)._iterspecs())) == 3
    assert len(list((ch & ch | ch & ch)._iterspecs())) == 4
    assert len(list((ch | ch & ch | ch)._iterspecs())) == 4
    assert len(list(((ch | ch) & ch)._iterspecs())) == 3
    assert len(list((ch | (ch & ch))._iterspecs())) == 3

    facet = alt.Chart("#").mark_bar().facet(column="test:N")
    assert len(list(facet._iterspecs())) == 1
    assert len(list((ch | (ch & facet))._iterspecs())) == 3

    repeat = alt.Chart("#").mark_bar().repeat(column=["test"])
    assert len(list(repeat._iterspecs())) == 1
    assert len(list((ch | (ch & repeat))._iterspecs())) == 3


def test_iterspecs_data():
    a = alt.NamedData("a")
    b = alt.NamedData("b")
    ch = alt.Chart(a).mark_bar()

    assert next(ch._iterspecs())[1] == a
    assert [d for _, d in (ch | ch)._iterspecs()] == [a, a]
    assert [d for _, d in (ch & ch)._iterspecs()] == [a, a]
    assert [d for _, d in (ch & ch.properties(data=b))._iterspecs()] == [a, b]
    assert [d for _, d in (ch & (ch.properties(data=b) & ch))._iterspecs()] == [a, b, a]

    facet = ch.facet(column="test:N")
    assert [d for _, d in facet._iterspecs()] == [a]
    assert [d for _, d in (ch | facet.properties(data=b))._iterspecs()] == [a, b]


def test_iterchannels():
    ch = alt.Chart("#").mark_bar().encode(x="x:Q", y="y:N")
    assert len(list(ch._iterchannels())) == 2
    assert len(list(ch.encode(text="z:N")._iterchannels())) == 3
    assert len(list(ch.facet(column="test:N").spec._iterchannels())) == 2
    assert len(list(ch.facet(column="test:N")._iterchannels())) == 3


def test_fields():
    ch = alt.Chart("#").mark_bar().encode(x="x:Q", y="y:N")
    assert len(list(ch._fields())) == 2
    assert len(list(ch.facet(column=alt.Column("z:N"))._fields())) == 3
