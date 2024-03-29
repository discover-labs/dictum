# Union Dimensions

Oftentimes a dimension spans multiple tables. This is usually the case with time dimensions.
If you think about it, `order_date` and `user_signup_date` are the same thing: just
an event time. In the current model, you can't calculate both signups and revenue by
month: order's "month" and signup "month" are not connected.

The same goes for order and user `channel`. There's no `channels` table in the schema,
for some reason they are just stored as a text value.

In a classic dimensional warehouse this would be solved by creating the `channels` table
an replacing the values in `orders` and `users` with a surrogate key. It's also a common
practice to create a `calendar` dimension table and linking all the dates to it.

This is a good approach and would work here, but it's also very tedious. Dictum
allows you to declare "virtual" dimensions called _Unions_. Just like normal dimensions,
they have an ID, a name and an optional description.


## Declare a union

Let's declare a union for time dimensions. Unions are declared at the root of the model
file.

```{ .yaml title=project.yml hl_lines="5 6 7 8 9" }
--8<-- "snippets/union_dimensions/union.yml"
```

To add a dimension to the union, you need to set the `union` attribute on that dimension.

```{ .yaml title=project.yml hl_lines="9 19" }
--8<-- "snippets/union_dimensions/dimensions.yml"
```

Now you can just use `date` dimension to query both metrics:

```py
(
    tutorial.select("revenue", "users")
    .by("date", "datepart('year')", "year")
)
```

--8<-- "snippets/union_dimensions/select_by_union.html"


## Think about how you name the metrics

When you create a time union, metric names become especially important. Right now, we
have a metric named `Number of Users`. Previously, you'd aggregate that by
`User Signup Date`, which makes sense. But now we also have an abstract `Date` dimension.
What does `Number of Users by Date` actually mean if you don't know about about the union
and it's members?

A good solution to that is to create a different metric that's basically a copy of
`Number of Users`, but named as an event. `User Signups by Date` is much clearer to the
end-user.

```{ .yaml hl_lines="8 9 10 11" }
--8<-- "snippets/union_dimensions/users.yml"
```
