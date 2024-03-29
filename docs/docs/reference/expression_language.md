# Expression language reference

Dictum expression language is used to define calculations —
[Measures](../concepts/model/measure.md),
[Dimensions](../concepts/model/dimension.md) and
[Metrics](../concepts/model//metric.md).
It's designed to be as similar as possible to SQL, but we should stress that it
is __not__ SQL. It's transformed to SQL by the database connection, but it's not passed
as-is to your database.

The main consideration with making the query language was simplicity and ease of support.
We'd like to support as many database backends as possible and having a small language
with a small number of functions makes sure that it's easy to support them. Another
reason to keep it small is to encourage users to prepare their data beforehand. If you
need to do complex stuff, use SQL. Things unrelated to the data model (complex processing)
don't belong with the data model.


## Literals

There are `string`, `integer` and `float` literals.

Strings are enclosed by single quotes (`'`): `'this is a string'`.

Integers are numbers without a floating point part: `12`, `42`, `9876` are all integers.
Floats are numbers with a floating point part, for example, `3.14`.


## References

You can reference columns and other calculations in calculation expressions.

To reference a column by name, just use that name: `amount`, `created_at`. If your column
is not a valid identifier, you can, like in SQL, surround it with double-quotes `"` to
escape: `"Column Identifier"`.

Measure and Metric references are prepended by `$`: `$revenue`. Because the line between
them is blurry, the notation is the same — Dictum will figure out what you mean.

Dimension references are prepended by `:` — `:sale_date`, `:channel`.

!!! info
    Operator names, column names and functions are case-insensitive. Calculation names
    are case-sensitive.

## Operators

### Arithmetic

Standard arithmetic operators are supported: `+`, `-`, `*`, `/`, `%` (division remainder),
`//` (floor division, or integer division), `**` (exponentiation, or power).

!!! important
    Division in Dictum works the same way as in Python 3: when you divide a value by an
    integer, the denominator is converted into float, e.g. `1 / 2 == 0.5`.

    Some database engines, like SQLite and Postgres have different semantics. For them,
    division works like this: `1 / 2 == 0`. Dictum overrides database engine semantics
    for consistency.

### Comparison

`>`, `<`, `>=`, `<=` are supported. Equals operator can be written as `=` or `==`. Not
equals is `!=` or `<>`.

### Boolean operators and ternary expressions

Boolean operators are `not`, `and`, `or`

`in` and `not in` are written the same way as in SQL: `x in (1, 2, 3)`.

Ternary expression `case when x then y else z end` is supported both with and without
`else` part.

!!! info
    `case x when y then z else p end` form is not suppoted yet.

!!! info
    There's no string concatenation operator (`||`) yet.


## Functions

### Aggregate

These are the functions that are used in measures to define aggregations.

!!! info
    To produce correct SQL, measure expressions need to produce an aggregate. Dictum
    doesn't check the expressions you wrote, so they may fail at runtime if they fail to
    produce an aggregation.

All the standard SQL aggregates are supported:

- `sum`
- `avg`
- `min`
- `max`

`count` function works differently than in SQL. To do `count(*)`, you call it without
arguments: `count()`. `count(distinct x)` is a separate function: `countd(x)`.


### Mathematical

- `abs` — absolute value.
- `floor` — removes the floating-point part of a float and returns a number that's
  closer to `0`.
- `ceil` — like `floor`, but in the opposite direction.

### Type casting

The expression language doesn't support standard SQL `CAST(x AS y)` construct, there are
specialized functions for each type: `toInteger`, `toFloat`, `toDate` and `toDatetime`.

### Dates

`datetrunc` function returns a date truncated to a given level of detail (part), e.g.
`datetrunc('month', toDate('2021-12-25')) -> '2021-12-01'`. The available parts are:

- year
- quarter
- month
- week (starting on Monday)
- day
- hour
- minute
- second

`datepart` function returns an integer of a given part of the date. The supported parts
are the same as for `datetrunc`.

!!! warning
    ISO standard defines first week of a year as the first week that has a Thursday in
    it. The first week always contains January 4th. Not all databases comply with this
    standard, and it would be very tedious to implement it per backend, so be aware
    then the behaviour of `week` part in `datepart` is backend-specific and corresponds
    to however the underlying database engine defines it.

`datediff` function calculates date difference at a given level (same supported parts).
The behavior is the same as SQL `datediff`: the difference between December 31, 23:59
and January 1, 00:00 next year is 1 year, 1 day, 1 month etc. You can say that it
calculates how many times a date part changed between two dates.

`now()` and `today()` return current timestamp and date.
