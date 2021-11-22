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

### Dimension aliases

If you want to transform the same dimension in multiple ways yielding multiple columns,
you have to give it an alias. Otherwise the result set will contain duplicate column
names, which nobody will be happy about.

```sql
select revenue
by sale_date with datepart('year') as year,
   sale_date with datepart('quarter') as quarter
```


## `WHERE` clause

`WHERE` clause applies filters to dimensions. The general syntax of each condition
is `dimension_name IS filter`. Conditions are separated by comma (`,`).

```sql
select revenue
where order_amount is atleast(100),
      customer_country is in('India', 'China')
```

!!! tip
    `in` here is a built-in filter. It is a function identifier, not an operator.


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
