# Query Language Reference

Hyperplane query language allows human programmers to request information from the data
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

### Top-K queries

You can add a `TOP n` qualifier to a grouping.

To select `revenue` and `orders`, but only for top-10 countries by revenue:

```sql
select revenue, orders
by top 10 country on revenue
```

If there's only one metric, `on` is not necessary:

```sql
select revenue
by top 10 country
```

You can use `top` to multiple groupings.

```sql
select revenue
by country, top 10 city
```

!!! info
    `LIMIT` is just a shorthand

```sql

select number_of_people
by country,
    top 10 city

select number_of_people
by top 10 country, top 1 city, district
```

### Dimension transforms

You can apply additional transforms to dimensions. The syntax for a tranformed grouping
is `dimension_name WITH transform`.

```sql
select revenue
group by sale_date with datetrunc('year'),
         amount with step(1000)
```

!!! tip
    If a transform takes no arguments, parentheses are optional. `sale_date with year()`
    is the same as `sale_date with year`.


## `WHERE` clause

The `WHERE` clause applies filters to dimensions. The general syntax of each condition
is `dimension_name IS filter`. Conditions are separated by comma (`,`).

```sql
select revenue
where order_amount is atleast(100),
      customer_country is in('India', 'China')
```

!!! tip
    `in` here is a built-in filter. It is a function identifier, not an operator.


## `ORDER BY` clause

The `ORDER BY` clause is used to order the results. Identifiers here must be in either
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
