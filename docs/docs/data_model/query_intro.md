# Query Introduction

The goal of Dictum is to give it's users an opportunity to ask questions about
various business metrics on an arbitrary level of detail. To better understand the
context the data model exists in, let's first see how these questions are formulated.

Dictum queries are structured objects. There are many ways to query Dictum store,
including [GraphQL API](../reference/graphql.md),
[Python code](../reference/python_api.md) and a special
[SQL-like query language](../reference/query_language.md). Here we'll use the latter as
an example. The query language is especially useful when you're developing you data
model and need to test that things are working as expected.


## Metrics and dimensions

A query needs at least one metric to calculate. The simplest query looks
something like `give me Revenue`, so:

```sql
select revenue
```

Then, we can start drilling into the details. Let's look at Revenue by marketing channel:

```sql
select revenue
group by channel
```

Things you group your metrics by are called `dimensions`. You can request any number of
dimensions that are compatible with the metrics. Metric-dimension compatibility depends
on your data schema and business domain. For example, revenue by product category or
customer city makes sense. Number of user signups by product category does not — there's
no connection. Dictum tracks these dependencies and will let you know which
metrics and dimensions can be added to the query next.


## Filters

What if we're only interested in revenue for orders larger than $100?

```sql
select revenue
where order_size is atleast(100)
group by channel
```

Filters have parameters, so they're presented as function calls. Unlike with normal
functions, we don't _pass_ dimensions as arguments, we _apply_ them to a dimension.


## Dimension transforms

What about Revenue by Date? It would be nice to let the user request metrics by any date
unit: year, quarter, month, week etc. You can always define separate dimensions for this,
but there's another way: query-time transforms.

```sql
select revenue
where order_size is atleast(100)
group by "date" with datetrunc('month')
```

We're telling Dictum that we want to request `date` by month. Let's add another dimension
and another transform.

```sql
select revenue
where order_size is atleast(100)
group by
         "date" with datetrunc('month'),
   order_amount with step(10)
```

The `step` transform is used to discretize continuous dimensions — think of it as putting
values into bins. You give it the step size and get results like `0` for `[0; 10)`, `10`
for `[10;20)` etc.

!!! tip
    You may have noticed that these queries are missing the `FROM` clause. This is because
    we query our data model as a whole. The user doesn't have to worry about tables and joins.
