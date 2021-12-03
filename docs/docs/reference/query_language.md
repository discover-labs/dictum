# Query Language Reference

Dictum query language allows human programmers to request information from the data
model. Text queries are compiled into the same `Query` object that can be sent to the
server's web API.

!!! info
    This query language officially doesn't have a name, because we have enough
    `whateverQL`s already.


## `SELECT` clause

The `SELECT` clause is used to request metrics. Any identifier in the select list is
interpreted as a metric ID.

```sql
select revenue, orders
```

!!! important
    Keywords, transform and filter names are case-insensitive, identifiers are case-sensitive.


## `GROUP BY` clause

The `GROUP BY` clause is used to request dimensions. The first identifier in each grouping
is interpreted as a dimension ID. Groupings are separeted by comma.

```sql
select revenue, orders
group by country, city
```

!!! tip
    The `GROUP` keyword is optional, you can just write `by customer_country, customer_city`.

### Dimension transforms

You can apply additional transforms to dimensions. The syntax for a transformed grouping
is `dimension.transform(arg1, arg2, argN, ...)`.

```sql
select revenue
by sale_date.datetrunc('year'),
   amount.step(1000)
```

!!! tip
    If a transform takes no arguments, parentheses are optional. `sale_date.year()`
    is the same as `sale_date.year`.

### Dimension aliases

When you apply dimension transforms, Dictum will give the resulting column a reasonable
default name. If you don't like this default name, you can give it an alias:

```sql
select revenue
by sale_date.year as year
   sale_date.quarter as quarter
```


## `WHERE` clause

`WHERE` clause applies filters to dimensions. Filters are similar to transforms, they
are just transforms that yield a boolean value. Multiple conditions are separated by
comma (`,`).

```sql
select revenue
where order_amount.ge(100),
      customer_country.in('India', 'China')
```

### Filter operators

In the snippet above we're using `ge` filter, which stands for "greater than or equals".
This is kind of ugly, so there's an alternative operator syntax, which will give you the
same result:

```sql
select revenue
where order_amount >= 100,
      customer_country in ('India', 'China')
```

There are `=`, `<>`, `>`, `>=`, `<`, `<=`, `in`, `is null`, `is not null` operators,
which are used just like in SQL. It's important to remember though, that this is just
syntactic sugar and in the end `ge` filter is used.


## `ORDER BY` clause

`ORDER BY` clause is used to order the results. Identifiers here must be in either
`SELECT` or `GROUP BY` to be available for ordering. `ASC` and `DESC` qualifiers are
supported, default being `ASC`.

```sql
select revenue
by customer_country
order by customer_country desc
```

## `LIMIT` clause

The `LIMIT` clause is used to limit the number of results returned from the server.
The basic form is `LIMIT number`.

To select top 10 countries by revenue:

```sql
select revenue
by customer_country
order by revenue desc
limit 10
```


## Built-in filters and transforms
