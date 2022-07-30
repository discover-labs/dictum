# Reusable expressions

Let's add some more measures to `orders`. We have a `user_id` there, so we can calculate
number of unique users who's made an order. If we divide revenue by that, we get ARPPU —
Average Revenue per Paying User.

In SQL, it would be something like this:

```sql
--8<-- "snippets/reusable_expressions/sql.sql"
```

That's a lot of repetition. In Dictum, you don't have to repeat the expressions:
they can reference each other.

```{ .yaml title=project.yml hl_lines="12 15" }
--8<-- "snippets/reusable_expressions/measures.yml"
```

In the expression language, we use the `countd` function instead of SQL
`count(distinct x)` syntax.

You can reference measures by their ID prepended with a `$` symbol, like this: `$revenue`.
Since measure reference is just an expression, you can use it in expressions just like
constants and columns.
There are two limitations to this:

- You can only reference measures that are declared on the same table.
- A measure can't reference itself, so circular references will result in an error.

!!! tip
    If you need to declare a calculation that involves measures from multiple tables,
    read about [Metrics](./metrics_and_measures.md).

Now you can query ARPPU, for example, in time:

```py
(
    tutorial.select("revenue", "unique_paying_users", "arppu")
    .by("order_created_at", "datepart('year')", "year")
)
```

--8<-- "snippets/reusable_expressions/arppu.html"
