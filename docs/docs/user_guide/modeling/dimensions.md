# Add dimensions to your model

Just calculating total revenue is not very useful. You'll certainly want to calculate it
across time and break it down by other attributes. So, let's do that.


## Add a time dimension

Orders have time that they were made at. We might want to look at revenue per day, week,
month, year etc. So, let's add a time dimension to our model.

```{ .yaml title=project.yml hl_lines="13 14 15 16 17"}
--8<-- "snippets/dimensions/time_dimension.yml"
```

Like measures, dimensions are added under a separate `dimensions` section. Each dimension
has a unique id that you define (in this case, `order_time`). The expression is just a
reference to the `created_at` column on orders.

In addition to `name` and `expr`, there's another field that's required for a dimension,
and that is `type`. In this case, the type of `order_time` is `time`.


## Dimension types

- `time` — anytime you have a column of type `date` or `datetime`/`timestamp`, you should
  use this type. You'll be able to view your metrics across time, at any level of detail
  (months, days, years etc.)
- `ordinal` — this means that the dimensions consists of a number of discrete values
  that are intrinsically ordered. An example of ordinal values are bins. Each bin is a
  discrete separate entity, but there's an order to bins, you can say which bin comes
  "before" and which "after".
- `nominal` — this is a discrete dimension that doesn't have any natural ordering. Think
  user names, marketing channels, product categories etc.
- `continuous` — this is a quantity that can take any numeric value, so it's continuous,
  not discrete. Usually continuous dimensions are used with a `step` transformation,
  which we'll discuss later.


## Add more dimensions

Let's add all the info that we have in the `orders` table. First, we have an obvious
candidate: the `channel` column. This is the marketing channel this order was assigned
to.

```{ .yaml title=project.yml hl_lines="18 19 20 21" }
--8<-- "snippets/dimensions/other_dimensions.yml"
```

Channel's type is `nominal`, because we can't give it an order. `facebook` doesn't come
"before" `instagram` of vice versa.

```{ .yaml title=project.yml hl_lines="22 23 24 25" }
--8<-- "snippets/dimensions/other_dimensions.yml"
```

Another, less obvious candidate, is `amount`. Same columns can be used in both measures
and dimensions. You can calculate sum of order amounts and care about order size as a
dimension at the same time. For example, you might want to know which orders — large or
small — bring your company more revenue.
