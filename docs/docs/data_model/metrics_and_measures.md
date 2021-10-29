# Metrics and Measures

Up until this point, we only declared measures. Measures are just aggregations defined
on a table. By default, all measures are automatically promoted to metrics. When you
declare a measure, a metric with the same name is created automatically.

If we look at Revenue, what we did before is just a shorthand for this:

```{ .yaml hl_lines="1 2 3 4 10 11" }
--8<-- "snippets/metrics_and_measures/explicit_revenue.yml"
```

Here, we define two items:

- An aggregation on `orders` table called `orders_amount_sum`. It doesn't have any
  business meaning — it's just an aggregation.
- A metric called `revenue` which has a meaning in the context of business. Note that
  it's not connected to any table.

Metrics are what users interact with, measures are just an implementation detail of
metrics. But, because most metrics are like Revenue here, just a reference to a measure,
all measures are implicitly considered metrics.

To prevent a measure showing up amoung metrics, you set `metric: false` attribute.


## Add session-based metrics

Let's calculate a _real_ metric, one that is a calculation of two measures declared on
different tables. We'll call it `Percentage of Paying Users` and it's defined as
`Unique Paying Users` divided by `Unique Active Users`. And `Unique Active Users`
is just a number of users that had at least one session on whichever level of detail
a user selects.

So, let's first define the base measures.

```{ .yaml }
--8<-- "snippets/metrics_and_measures/user_sessions_table.yml"
```

`Unique Active Users` is a useful metric by itself, so we won't hide it from users.


## Derive a metric from measures

Now we can finally add `Percentage of Paying Users`.

```yaml
--8<--- "snippets/metrics_and_measures/ppu.yml"
```


## Understand how queries are executed

To better understand why there's a distinction between metrics and measures, let's
consider how metrics like `PPU` are calculated.

First, the Hyperplane computes measures on the requested level of detail. If we want to
see `PPU` and `AU` by month, it comes down to two SQL queries:

```sql
--8<-- "snippets/metrics_and_measures/ppu_base.sql"
```

Now Hyperplane needs to merge them on the `date` column and calculate the metrics.
This is done with a `FULL OUTER JOIN`.

```sql
--8<-- "snippets/metrics_and_measures/ppu_merge.sql"
```

!!! warning
    Generally, Hyperplane tries to leave as much calculation as possible to the database
    backend.

    SQLite doesn't support `FULL OUTER JOIN` construct, so the backend will materialize
    the above queries into a Pandas DataFrame and calculate everything in Pandas.

So, aggregations calculated at the first step are measures, and metrics are just calculations
on measures done after the merge step.
