# Aggregate Dimensions

Some dimensions you might want to have in your model can be derived from measures.
For example, you might want to see the distrubution of users by how many orders they
made.

This is also useful for cohort analysis: you can calculate `First Order Date` dimension
for each user, and then the difference between the user's `First Order Date` and
`Order Date` on orders.

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

```{ .yaml hl_lines="3 4 5 6 7 8 9" }
--8<-- "snippets/aggregate_dimensions/measures.yml"
```

`min_sale_date` doesn't make sense as a metric, so we set `metric: false` to hide it from
users. `n_orders` on the other hand is absolutely useful.


## Create aggregate dimensions

```{ .yaml hl_lines="11 15" }
--8<-- "snippets/aggregate_dimensions/dimensions.yml"
```

Yes, it's that simple. You can just drop a measure into the dimension expression and
it will be grouped by the table's primary key and joined in.


## Use dimensions in other dimensions' expressions

In [Reusable Expressions](reusable_expressions.md) we talked about how measures can be
referenced in other measures' expressions.

It also works with dimensions, but in addition to dimensions declared on the same table
you can use dimensions from any related table, as long as there's a single unambiguous
join path to it. To reference a dimensions, prefix it's ID with a colon (`:`).

```{ .yaml hl_lines="9" }
--8<-- "snippets/aggregate_dimensions/datediff.yml"
```

Now users can do basic cohort analysis. For example, they can view how much revenue a
particular user cohort brings over time, or compare between those cohorts.
