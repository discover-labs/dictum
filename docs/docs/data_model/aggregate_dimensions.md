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


## Create aggregate dimensions and measures that support them

Dimensions derived from measures are really simple to create. You can just reference a
measure from any table that's related to the dimension's table in the expression, and
this measure will be calculated at the level of the table's primary key.

```{ .yaml hl_lines="3 4 5 6 7 8 9 18 19 20 21 22 23 24 25 26" }
--8<-- "snippets/aggregate_dimensions/user_orders_count.yml"
```

!!! info
    Note that `n_orders` is a metric, but `min_order_date` is not — we want to hide it from
    users.
