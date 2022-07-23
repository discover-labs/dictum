# Measure

A measure is an aggregation defined on a single fact [table](table.md).

!!! info
    Dictum doesn't force you to use any particular data modeling style
    (e.g. a [Star Schema](https://en.wikipedia.org/wiki/Star_schema)).
    Each table can be a fact table or a dimension table in different
    contexts.

You can think of measures as building blocks for [metrics](metric.md).

A metric can equal a measure if it can be calculated from a single
table, but this is not always the case. For example, you can have
two measures that are also very important metrics:

- `revenue` = `sum(amount)` on table `orders`
- `active_users` = `countd(user_id)` on table `user_sessions`

Then you can define a metric that is _not_ a measure:

- `revenue_per_active_user` = `$revenue / $active_users`

As you can see, the last calculation is by definition not bound
to any single table — it uses information from two tables at once!
By clearly separating measures and metrics, Dictum allows you to
define such calculations, which can be then used to define further
metrics etc.

Because most measures will also be metrics (like `revenue` in the
example above), you can define them in two places: separately from
the host table together with other metrics or in the table definition
file (see [below](#defining-measures-as-metrics)).

## Schema

```yaml
name: |
    string, required
    Human-readable descriptive display name for a metric

description: |
    string, optional
    A longer description for documentation purposes.

expr: |
    string expression, required
    An aggregate expression, e.g. sum(amount).
    A non-aggregate expression will result in an error.
    For details, see Expression language reference.

type: |
    float | int | date | datetime | bool | str, defaults to float
    The data type of the calculation. Because most measures are
    numerical in nature, defaults to float.

format: |
    string or dict, optional
    Formatting information (see Formatting).

missing: |
    whatever type is specified in the type field, optional
    If a query returns a missing value (NULL) in some slice, it will
    be replaced with this value.

metric: |
    boolean, defaults to false
    If true, a measure that's defined together with the table
    (under "measures" section) will be also treated as a metric.

filter: |
    string expression, optional
    Apply this filter to the source table before calculating the
    expression. For explanation, see below.

time: |
    string, optional
    A dimension that will be treated as the default time dimension
    for this measure. For explanation, see below.

table: |
    string, required
    Only required for measures that are defined in a separate file
    in the `metrics` directory. Specifies which table this measure
    should be calculated from.
```

## Formatting

See [Formatting](formatting.md).

## Defining measures as metrics

Metrics are very important. So important that by default, each one
gets a separate file in your project. But some (if not most) metrics
can be defined as simple measures. This leads to a situation where
the `metrics` folder only contains weird stuff like `arppu.yml` and
`regs_to_orders_ratio.yml`, but all the important things, like revenue,
are hidden in table files.

To avoid this, Dictum supports two ways of promoting measures to metrics.

```yaml
# tables/orders.yml
...
measures:
  revenue:
    name: Revenue
    expr: sum(amount)
    metric: true  # this measure is a metric!
```

```yaml
# metrics/revenue.yml
name: Revenue
expr: sum(amount)
table: orders  # this metric is a measure!
```

Without `table` specified, Dictum won't allow you to reference columns
in the metric expression, which makes sense, because columns exist
only in the context of tables.


## Expressions

The `expr` key is the most important part of measure definition.
It defines how to aggregate the data to get the desired result.

Expressions are written with the
[expression language](../../reference/expression_language.md).
It is very similar to SQL expressions (what you write when you
select columns in a SELECT query), but it isn't. In the end Dictum
_compiles_ it to SQL, but don't think that it's passed to your
database as-is.

You can see [the reference](../../reference/expression_language.md)
for details, but these are the major differences:

### `countd` function

There's no `distinct` operator. To calculate `count(distinct user_id)`,
you need to use `countd` function: `countd(user_id)`.

!!! info
    Functions in the expression language are case-insensitive.
    `countd(user_id)`, `COUNTD(user_id)` and `CountD(user_id)`
    mean the same thing.

### Related column references

You can reference columns of the related tables in the expression.

For example, you might have an `orders` table that has a related table
`users`:

```yaml
# tables/orders.yml
source: orders
related:
  product: product_id -> products.id
```

Imagine that it's very important for the growth of you business that
you customers buy products from all categories. You might define
a metric called "Unique Active Categories". A reference to the
category is stored in the `products` table, `category_id` column.

You can define this measure as `countd(product.category_id)`.

### Measure references

You can also reference other measures defined on the same table
from within the expression.

If you define two measures on a table:
- `revenue` = `sum(amount)`
- `unique_paying_customers` = `countd(user_id)`

Then you can defined a third measure:
- `revenue_per_paying_customer` = `$revenue / $unique_paying_customers`

Measures are referenced by their identifier, the key under which they
are defined in the `measures` section of a table. The identifier is
prepended by the `$` symbol to hint that this is a reference to a measure.

## Missing values

The `missing` key controls what happens if in some slice of data
you measure's value is `NULL`.

Imagine that you have a metric called
"Average Revenue per Active User" that's defined as `$revenue / $unique_active_users`.
What if in some particular day or hour there were no orders at all?
In that situation `$revenue` would be `NULL` and the value of your metric
would also be `NULL`.

If you want it to be `0` instead, set `missing: 0` on `revenue`.

## Measure Filter

Dictum treats each measure as a kind of a virtual fact table.
Some measures might be concerned with all the rows of a particular table,
while others only with some of them.

For example, if you have an `orders` table and want to calculate how
many orders were cancelled each day, you can do it in several ways.
The most obvious way is to define the measure as `count(cancelled_at)`,
assuming that the cancellation timestamp is missing for non-calcelled
orders.

If you compute this measure by `cancelled_at` truncated to days, you
will get a weird `NULL` value in the result: the database will also compute
how many cancelled orders were in the case where an order wasn't cancelled.

To avoid this, you can filter out these rows alltogether for this measure:

```yaml
name: Number of Cancelled Orders
expr: count()
missing: 0
filter: cancelled_at is not null
```

## Default time dimension

Time is a very special thing. In some sense, there's only _one time_
we can think of — all events and facts are located somewhere on
the singular timeline.

When we explore the data, most of the time we don't want to think about
the particular time dimensions a measure is related to. Yes, you might want
to see _Revenue by User Registration Date_, but most of the time you
want just _Revenue by Date of Revenue_. Data people might remember that
date of revenue is the same as the date when an order was made, but
business people want to just _see the quarterly revenue_.

To reflect these deeply philosophical facts, Dictum supports specifying
a default time dimension for measures. If such an option is present,
Dictum will allow users to specify [generic dates](dimension.md#generic-dates)
in the query.

Some examples:

```yaml
# tables/orders.yml
name: Revenue
expr: sum(amount)
time: order_date
```

```yaml
# tables/users.yml
name: User Registrations
expr: count()
time: user_registration_date
```
