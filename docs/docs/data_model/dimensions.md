# Dimensions

Just calculating total revenue is not very useful. You'll certainly want to calculate it
across time and break it down by other attributes. So, let's do that.


## Add a time dimension

Orders have time that they were made at. We might want to look at revenue per day, week,
month, year etc. So, let's add a time dimension to our model.

```{ .yaml title=project.yml hl_lines="14 15 16 17 18"}
--8<-- "snippets/dimensions/time_dimension.yml"
```

Like measures, dimensions are added under a separate `dimensions` section. Each dimension
has a unique id that you define (in this case, `order_created_at`). The expression is
just a reference to the `created_at` column on `orders`.

In addition to `name` and `expr`, there's another field that's required for a dimension,
and that is `type`. In this case, the type of `order_created_at` is `datetime`.

!!! important
    All calculations (metrics, measures and dimensions) have a type. For dimensions you're
    required to specify a type, metrics and measures have a default `number` type, but
    you can change it.

    Types together with formats affect how your data is displayed. There are

    - numeric types: `number`, `decimal`, `percent`, `currency`;
    - time types: `date`, `datetime`;
    - and a `string` type.

    For a more thorough overview of formatting and types, see [Types and Formatting](./types_formatting.md).


## Query Revenue by Order Date

Now we can query Revenue by Date:

```py
tutorial.select("revenue").by("order_created_at")
```

--8<-- "snippets/dimensions/query_revenue_by_date.html"

Oops, this doesn't look like what we wanted to achieve. `order_created_at` dimension
is very granular: each value is a timestamp, including seconds. We probably want to
aggregate this at some other level, like, for example, years or quarters.

### Dimension transforms

You can define additional transforms for dimensions at query time. Let's truncate
`order_created_at` timestamp to the level of years.

```py
tutorial.select("revenue").by("order_created_at", transform="datetrunc('year')")
```

--8<-- "snippets/dimensions/query_revenue_by_date_transform.html"

This is much better. As you can see, a transform is defined as a function call with some
arguments. There are many built-in tranforms for different types of dimensions, and you
can even write your own.

!!! info
    For more on transforms, see [Transforms](./transforms.md)

### Dimension aliases

What if we wanted to group revenue by year and month, in separate columns?

You can add as many `.by(...)` calls as you want to add multiple groupings. There's also
a `datepart(part: str)` transform, which does exactly what we want. The only problem is
that we'd have to use the same dimension twice, and Pandas doesn't want us to have
duplicate column names (and honestly, we don't want them either).

```py
(
    tutorial.select("revenue")
    .by("order_created_at", transform="datepart('year')", alias="year")
    .by("order_created_at", transform="datepart('month')", alias="month")
)
```

--8<-- "snippets/dimensions/query_revenue_by_date_alias.html"

The solution is to give the resulting column an alternate name, which is done by
specifying an `alias`. Aliases can be used with or without an accompanying transform.


## Add more dimensions

Let's add all the info that we have in the `orders` table. First, we have an obvious
candidate: the `channel` column. This is the marketing channel this order was assigned
to.

```{ .yaml title=project.yml hl_lines="21 22 23 24" }
--8<-- "snippets/dimensions/other_dimensions.yml"
```

Channel's type is `string`.

```{ .yaml title=project.yml hl_lines="25 26 27 28 29" }
--8<-- "snippets/dimensions/other_dimensions.yml"
```

Another, less obvious candidate, is `amount`. Same columns can be used in both measures
and dimensions. You can calculate sum of order amounts and care about order size as a
dimension at the same time. For example, you might want to know which orders — large or
small — bring your company more revenue.

Amount's type is `currency`. We can also make it `number`, but `currency` type will
display the amount as money. When a calculation's type is `currency`, you have to specify
which currency it is. Here, it's `USD`.

!!! tip
    Currencies are specified as a 3-letter code as defined by
    [ISO-4217 standard](https://en.wikipedia.org/wiki/ISO_4217).

Now that we know how to use `currency` type, we should also update `revenue`:

```{ .yaml title=project.yml hl_lines="14 15" }
--8<-- "snippets/dimensions/other_dimensions.yml"
```

### Pivoted query

Python API that we're using (`Project` class) is mostly created for data analysts to use
while developing the data model and for quickly retrieving data for further analysis.
In these cases presentation is not that important, but sometimes it's good to have a
simple way to create a pivot table just to quickly check a metric or make an export to
Excel.

```py
(
    tutorial.pivot("revenue")
    .rows("channel")
    .columns("order_created_at", "datepart('year')", "year")
)
```
--8<-- "snippets/dimensions/pivot.html"

It's the same as `select`, but you can specify which dimensions to display as rows, and
which as columns. Like `by`, `rows` and `columns` can be called multiple times to add
more levels to either of them.

```py
(
    tutorial.pivot("revenue")
    .columns("channel")
    .rows("order_created_at", "datepart('year')", "year")
    .rows("order_created_at", "datepart('quarter')", "quarter")
)
```

--8<-- "snippets/dimensions/pivot_nested.html"
