# Query Language Reference

Dictum query language allows human programmers to request information from the data
model. Text queries are compiled into the same `Query` object as described in the
[Query](../concepts/query/intro.md) section of the documentation.

!!! info
    This query language officially doesn't have a name, because we have enough
    `whateverQL`s already.


## `SELECT` clause

The `SELECT` clause is used to request metrics. Any identifier in the select list is
interpreted as a metric ID. Multiple metrics can be selected as long as they all share
all of the dimensions used in the query (in groupings and filters).

```sql
select revenue, orders
```

!!! important
    Keywords, transform and filter names are case-insensitive, identifiers are case-sensitive.

### Aliases

Metrics (and also dimensions) can be given a name with `as` keyword, just like in SQL.

```sql
select revenue, revenue.percent as "Revenue (%)"
```


## `GROUP BY` clause

The `GROUP BY` clause is used to request dimensions. Like metrics, dimensions can be
given an alias.

```sql
select revenue, orders
where city_is_capital
group by country, city as "Capital"
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

`WHERE` clause applies filters to the data. Filters are similar to transforms, they
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

<!--
## `ORDER BY` clause

`ORDER BY` clause is used to order the results. Identifiers here must be in either
`SELECT` or `GROUP BY` to be available for ordering. `ASC` and `DESC` qualifiers are
supported, default being `ASC`.

```sql
select revenue
by customer_country
order by customer_country desc
```
-->

## `LIMIT` clause

The `LIMIT` clause is similar to `WHERE`, but the filters are logically applied _after_
the resulting aggregated data table is constructed, not before. Therefore it is used
with metrics, not dimensions.

For now, `LIMIT` only supports two table transforms: `top` and `bottom`.

To select top 10 countries by revenue:

```sql
select revenue
by country
limit revenue.top(10)
```


### Nested top-k queries

Top and bottom limits can be nested:

```sql
select revenue
by country, city
limit revenue.top(10) of (country),
    revenue.top(3) of (city) within (country)
```

This query will give you top 3 cities per country, but only for the top-10 countries.
Note the `within` part: if it's not present and write just `revenue.top(3) of (city)`,
the the query will return only those rows that are both in the top-10 countries _and_
the top-3 cities globally, not _within_ each country.

The rule of thumb to remember is: __"of"__ is everything that's not __"within"__.
The query below will give you top-10 (region, city) pairs within each country.

```sql
select revenue
by country, region, city
limit revenue.top(10) within (country)
```

If both `of` and `within` are omitted, Dictum will assume what all dimensions are in
`of`.


## Dimension transforms

### Boolean

#### Comparison

```sql
select revenue
where order_amount.ge(100)
```

```sql
select revenue
where order_amount >= 100
```

The available transforms are:

- `eq` or `=`
- `ne` or `<>` or `!=` — "not equals"
- `gt` or `>`
- `ge` or `>=`
- `lt` or `<`
- `le` or `<=`

#### Value in set

There's a transform similar to SQL `in` operator:

```sql
select revenue
where country.isin('USA', 'Canada')
```

```sql
select revenue
where country in ('USA', 'Canada')
```

#### Boolean negation — `invert` or `not`

```sql
select revenue
where city_is_capital.invert
```

```sql
select revenue
where not city_is_capital
```

#### Null comparison — `isnull`, `isnotnull`

```sql
select revenue
where order_bonus_card.isnull
```

```sql
select revenue
where order_bonus_card is null
```

```sql
select revenue
where order_bonus_card.isnotnull
```

```sql
select revenue
where order_bonus_card is not null
```

#### `inrange`

Works the same way as SQL `between`.

```sql
select revenue
where order_amount.inrange(100, 1000)
```

### Date and time

#### `last` — date range until today

```sql
select revenue
where Time.last(30, 'day')
```

#### `datetrunc`

Truncates dates or datetimes to a given level of granularity.

```sql
select revenue
where Time.datetrunc('year')
```

Valid date part values are:

- `year`
- `quarter`
- `month`
- `week` (week number in year)
- `day` (meaning day of month)
- `hour`
- `minute`
- `second`

#### Truncating a datetime to a date

```sql
select revenue
by Time.date
```

is the same as

```sql
select revenue
by Time.datetrunc('day')
```

#### `datepart`

Extracts a part (as a number) from a date or datetime. Valid part
values are the same as above.

```sql
select revenue
by Time.datepart('month')
```

#### Short `datepart`

To avoid writing out the full `datepart`, you can just use transforms
named after the parts.

```sql
select revenue
by Time.year, Time.quarter
```

### Numeric transforms

#### `step`

Rounds the values of dimension to a given step size.
The query below will turn `42` and `49` into `40`.

```sql
select revenue
by order_amount.step(10)
```

## Metric transforms

### `total`

Computes the total value of a metric within a given combination of dimensions.

```sql
select revenue, revenue.total within (country)
by country, city
```

### `percent`

Divides metric value by the total value and outputs a percentage.

The query below will give you percentages such as each city within each
country adds up to 100%.

```sql
select revenue, revenue.percent within (country)
by country, city
```

The next query will give you the same value for each row within the same country
which will be the percentage of total revenue for that country.

```sql
select revenue, revenue.percent of (country)
by country, city
```
