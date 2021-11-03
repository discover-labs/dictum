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
has a unique id that you define (in this case, `order_date`). The expression is just a
reference to the `created_at` column on `orders`.

In addition to `name` and `expr`, there's another field that's required for a dimension,
and that is `type`. In this case, the type of `order_date` is `date`.

!!! important
    All calculations (metrics, measures and dimensions) have a type. For dimensions you're
    required to specify a type, metrics and measures have a default `number` type, but
    you can change it.

    Types together with formats affect how your data is displayed. There are

    - numeric types: `number`, `decimal`, `percent`, `currency`;
    - time types: `date`, `datetime`;
    - and a `string` type.

    For a more thorough overview of formatting and types, see [Types and Formatting](./types_formatting.md).


## Add more dimensions

Let's add all the info that we have in the `orders` table. First, we have an obvious
candidate: the `channel` column. This is the marketing channel this order was assigned
to.

```{ .yaml title=project.yml hl_lines="19 20 21 22" }
--8<-- "snippets/dimensions/other_dimensions.yml"
```

Channel's type is `string`.

```{ .yaml title=project.yml hl_lines="23 24 25 26 27" }
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

To see which orders — large or small — gave you the most revenue:

```sql
select revenue
by order_amount with step(100)
```

To see revenue in time:

```sql
select revenue
by order_date with month
```
