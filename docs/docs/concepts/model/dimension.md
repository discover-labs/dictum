# Dimension

A dimension is something that you can group and filter your
metrics by. A user registration date, order delivery address,
total number of orders a user made.

Most dimensions are just table columns, like `name` in the
`product_categories` table. The power of Dictum comes from the
fact that when you request _revenue by product category_, you don't
have to remember that you have to first join `products` by `product_id`
to `orders` and then `product_categories` by `category_id` to `products`.
Because all the information about table relationships is already
in your model, all you have to do is specify the dimension.

Dimensions are tied to tables, so unlike [measures](measure.md),
they can only be defined in the same file as the table, under
the `dimensions` key.

## Schema

```yaml
name: |
    string, required
    Human-readable descriptive display name for a dimension

description: |
    string, optional
    A longer description for documentation purposes.

expr: |
    string expression, required
    Must be an non-aggregate expression.
    An aggregate expression will result in an error.

type: |
    float | int | date | datetime | bool | str, required
    The data type of the calculation.

format: |
    string or dict, optional
    Formatting information (see Formatting).

missing: |
    whatever type is specified in the type field, optional
    Missing values (NULL) in the dimension will be replaced
    with value specified in this option.

union: |
    string, optional
    If present, this dimension will be treated as belonging
    to a union with this ID. The union must be defined
    in unions.yml. See below for explanation.
```


## Unions

Data in data warehouses is not always perfectly normalized.
If dimensions are tied to tables, it means that each dimension can
only exist in one table at a time, meaning that the data _must_
be normalized for Dictum to work.

So, for example, if you have a dimension called `country`, Dictum
will expect that there's some table holding a list of countries that
it can join to the fact tables.

What if your data _is_ denormalized, and `country` is just a literal
column in, say, `users` and `orders` table? Common sense tells us that
"France" in `users.country` and "France" in `orders.country` is the same
France. We might want to construct a query that gives us both number of
users and number of orders per `country`.

To connect the two columns we can define a thing called a _union_.
A union is like an alias for several other dimensions.

```yaml
# unions.yml
country:
  name: Country
  type: str
```

```yaml
# tables/users.yml
...
dimensions:
  user_country:
    name: Users's Country in Profile
    type: str
    expr: country
    union: country
```

```yaml
# tables/orders.yml
...
dimensions:
  order_country:
    name: Order Delivery Country
    type: str
    expr: country
    union: country
```

For a user querying Dictum, there are now 3 dimensions: a generic
`country`, a `user_country` and an `order_country`. So they can get
_number of users by country_, _number of orders by country_ and
_number of orders by user\_country_.


## Aggregate dimensions

!!! info
    This feature, while convenient, produces subobptimal queries.
    It's recommended that you materialize such information as a
    physical column and just use normal dimensions.

Some dimensions can be calculated from measures. Let's say you have
a measure called `revenue` and you want to calculate the number of users
per revenue bracket. That is, first you need to calculate `revenue`
on a per-user basis and then use that value as a dimension.

To do this, you can just use `$revenue` in the dimension expression:

```yaml
# tables/users.yml
...
primary_key: id  # primary_key is required for aggregate dimensions to work
dimensions:
  user_revenue_bracket:
    name: User Revenue Bracket
    description: |
      Revenue bracket for a user. The brackets are:
      [0, 10), [10, 100), [100, 1000), [1000, ...]
    type: string
    expr: |
        case when $revenue < 10 then '< 10'
             when $revenue < 100 then '< 100'
             when $revenue < 1000 then '< 1000'
             else '>= 1000'
        end
```
