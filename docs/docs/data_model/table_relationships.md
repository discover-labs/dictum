# Table Relationships

The real power of Dictum's declarative approach comes from being able to describe
table relationships and have the tool figure out the joins on it's own.


## Add a second table

Orders have a `category` attribute, but actual category names are stored in a separate
table. Let's add it.

!!! info
    Because our model has grown, at this point we'll show you only relevant parts of the
    config, not the whole thing.

```{ .yaml title=project.yml }
--8<-- "snippets/table_relationships/categories_table.yml"
```

!!! warning
    Note that you won't be able to reference a table in a relationship if it doesn't
    have a primary key declared.


## Add a relationship

Let's go back to orders. What if we wanted to calculate Revenue by category? In SQL,
we'd have to do a join. Here, we just declare a relationship.

```{ .yaml title=project.yml hl_lines="4 5 6 7" }
--8<-- "snippets/table_relationships/relationship.yml"
```

We add relationships under the `related` key. `category` here is just a name which we
can use in expressions to access columns on a related table. Relationship definition
consists of a `table` — this is the name of the table that we defined, _not_ the source.

```{ .yaml title=project.yml hl_lines="11 12 13 14" }
--8<-- "snippets/table_relationships/relationship.yml"
```

After the relationship is declared, we can access the related table's columns by
prefixing them with related table's name, like this: `category.name`

To query revenue by order category:

```sql
select revenue
by order_category
```

## Add another relationship

Let's quickly add the `users` table to the model.

```{ .yaml title=project.yml hl_lines=7 }
--8<-- "snippets/table_relationships/users_table.yml"
```

The only thing of note here is the new aggregate function `count`. It works the same way
as the SQL count, but when you want to do `count(*)`, you just call it without arguments:
`count()`. It will calculate the number of rows in the table it's declared on.

!!! tip
    You don't have to do `distinct` here. Because Dictum only allows foreign key to
    primary key joins, relationships never produce duplicates, given that your data are
    correct.

Now we can add a reference to `users` on `orders`.

```{ .yaml title=project.yml hl_lines="8 9 10" }
--8<-- "snippets/table_relationships/users_relationship.yml"
```

Previously we declared `category` directly on `orders` because category only means
something in the context of orders. But we could just as well declare it on `categories`
and the result would be just the same.

!!! tip
    If you have a single direct chain of relationships from a measure's "host" table to a
    dimension's "host" table, that dimension can be used with the measure.

To view revenue by user's sign-up channel:

```sql
select revenue
by user_channel
```
