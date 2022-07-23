# Aggregate Dimensions

Let's think about how the `users` table in a traditional data warehouse looks. Usually
data teams calculate various metrics per-user. How many orders did this user make?
What is their total order amount? When was the first order?

In Dictum there's a special kind of dimensions called aggregate dimensions. They are
created exactly for this purpose: calculating an existing measure per table row and
using _that_ as a dimension.

!!! warning
    Aggregate dimension calculations produce queries that will not perform very well.
    Although we support this use case for the sake of flexibility, it is strongly
    advised that you materialize them as columns in an upstream tool and then use them
    as a normal dimension.


## Create the necessary measures

Dimensions derived from measures are really simple to create. You can just reference a
measure from any table that's related to the dimension's table in the expression, and
this measure will be calculated at the level of the table's primary key.

First, we need to create the measures that will support them.

```{ .yaml hl_lines="4 5 6 7 8 9 10 11" }
--8<-- "snippets/aggregate_dimensions/measures.yml"
```

`min_order_date` doesn't make sense as a metric, so we set `metric: false` to hide it from
users. `orders` on the other hand is absolutely useful.


## Create aggregate dimensions

You can just drop a measure into the dimension expression and it will be grouped by the
table's primary key and joined in.

```{ .yaml hl_lines="11 15" }
--8<-- "snippets/aggregate_dimensions/dimensions.yml"
```

Now we can calculate number of users by how many orders they made:

```py
(
    tutorial.select("users")
    .by("user_order_count")
)
```

--8<-- "snippets/aggregate_dimensions/user_order_count.html"



## Use dimensions in other dimensions' expressions

In [Reusable Expressions](reusable_expressions.md) we talked about how measures can be
referenced in other measures' expressions.

It also works with dimensions, but in addition to dimensions declared on the same table
you can use dimensions from any related table, as long as there's a single unambiguous
join path to it. To reference a dimension, prefix it's ID with a colon (`:`).

```{ .yaml hl_lines="9" }
--8<-- "snippets/aggregate_dimensions/datediff.yml"
```

Now users can do basic cohort analysis. For example, they can view how many orders
particular user cohort made over time and compare between those cohorts.

```py
(
    tutorial.pivot("orders")
    .rows("user_first_order_date", "datetrunc('month')", "cohort_month")
    .columns("months_since_first_order")
    .where("user_first_order_date", "atleast('2021-11-01')")
)
```

--8<-- "snippets/aggregate_dimensions/order_cohorts.html"
