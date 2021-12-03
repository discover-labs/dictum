# Dictum

!!! quote ""
    In general usage, a __dictum__ (plural dicta) is an authoritative or dogmatic statement.

Dictum is an open-source semantic layer for your data. It serves as an authoritative,
single source of truth about the _meaning_ and _structure_ of your data, allowing you
to skip writing SQL and thinking about tables, colunms, joins and calculations,
concentrating entirely on the business problem at hand.

After describing how your data is stored with a YAML configuration file, you can start
asking questions like:

- How many signups per week do we have?
- How many users are there in each LTV bucket?
- How close is each sales manager to meeting their monthly sales target?

Dictum will translate them to a query (both SQL and non-SQL backends can be supported),
execute it and return the results.


## Where to start

If your team already uses Dictum and you want to learn how to query it, read the
[Query Guide](query/intro.md).

If you want to learn how to describe your data, read the
[Data model guide](data_model/getting_started.md).


## Querying

Dictum can be queried with a special [SQL-like query language](reference/query_language.md),
[Python query builder](reference/python_api.md), [GraphQL API](reference/graphql.md)
or by directly building a [Query object](reference/query.md).

=== "Query language"

    ```sql
    select signups
    where date.last(52, 'week')
    by date.datetrunc('week') as week
    ```

=== "Python query builder"

    ```py
    project = Project()
    date = project.dimensions["date"]
    (
        select("signups")
        .by(date.datetrunc("week"), alias="week")
        .where(date.last(52, "week"))
    )
    ```

=== "Query object"

    ```json
    {
        "metrics": [{"metric": "signups"}],
        "dimensions": [
            {
                "dimension": "date",
                "transform": {
                    "id": "datetrunc",
                    "args": ["week"]
                }
                "alias": "week"
            }
        ],
        "filters": [
            {
                "dimension": "date",
                "filter": {
                    "id": "last",
                    "args": [52, "week"]
                }
            }
        ]
    }
    ```


## Database connectors

Dictum includes database connectors for SQLite and Postgres. Any SQLAlchemy engine can
be easily adapted, overriding just a couple of database-specific functions. Additional
database connectors can be installed as plugins.


## Use cases

### Metrics Catalog

The traditional medium for consuming data are dashboards. When a user wants to look up
a metric or make a data-informed decision, they look for a relevant dashboard, switch a
couple of filters and get the result.

This works in smaller organizations or very simple business domains, but when a company
and variety of roles in it grow, a dashboard-making data team has two solutions:

- Build more and more dashboards to accomodate everyone. This is how you can end up with
  hundreds of them, which is difficult for users to navigate and for the team to maintain,
  resulting in outdated or broken dashboards being used.
- Add more and more knobs and switches to the existing dashboards. In almost every company,
  theres a "God Dashboard" with 30 different filters and parameters, because the users
  need to see the data in every possible combination of slices. These dashboards are
  usually slow, difficult to use and error-prone as a result.

Even if the team can manage this complexity, there's a "long tail" of requests from users,
the dreaded __ad-hocs__. They don't warrant a dashboard, because there's no pattern, but
in aggregate they take a lot of time and, most importantly, they are boring and
uninspiring to work on.

!!! question
    What is ARPPU for premium users over the age of 37 whose favorite product category
    is "rock climbing equipment" and who own a MasterCard?

What if there was a place where users could go, choose a metric and how they want to
break it down and get an instant answer? This place is Dictum web interface.

### Headless BI

In traditional Business Intelligence tools calculations on data are defined at the level
of each dashboard. Calculation and visualization are bundled together, often resulting
in a situation of the same metric being calculated in different ways.

!!! question
    Why is Q3 Revenue in "Operational Sales Report" and "Finance Quarterly Dashboard"
    different? One of them must be wrong!

There might be a good reason for this discrepancy: maybe "Revenue for Operations People"
includes orders made with an installment plan, but "Revenue for Finance People" doesn't.
Still, the analyst who made the dashboard for the Finance People didn't think to check
how "Revenue" is calculated in 6 other places.

Which metrics there are and how they are calculated is _organizational knowledge_: it
should be version-controlled, up-to-date, accessible and easily operationalized.
Documentation partially solves this problem, but what if documentation was stored
together with the code that defines the calculations? What if documentation and code
were actually _the same thing_?

Dictum serves as the single source of truth about your organization's metrics.
User-facing BI tools should be used for what they excel at: data visualization (no pun
intended). Metrics should be described and documented centrally, in the same place,
and consumed by downstream tools.

### Analytics Backend

GraphQL introduced the concept of frontend-directed API: the backend should be agnostic
about how it is used, and the frontend should define what the backend will return. This
allows further decoupling between front- and backend.

This approach works well for OLTP, when the app conserns itself with reading and writing
data related to singular objects. Some apps however include user-facing analytics, which
display aggregated data. GraphQL makes it difficult to define schemas for arbitrary
aggregations.

Dictum server includes a GraphQL API that does for aggregations what GraphQL itself
did for OLTP. If you have a custom analytical interface that aggregates data in many
different ways or has a lot of filters, you can use Dictum as a backend server for
it.

In addition to that, it can be used without the server as a Python library.


## Design considerations

Dictum was designed with several things in mind. It's unopinionated in some things
and very opinionated in others.

- __It doesn't make assumptions about your data stack.__ We all love dbt. Really. But
  it's stange to assume that everyone uses it. Dictum will work regardless of upstream
  tools you're using to transform your data. People who use SSIS also deserve good tools.
- __It doesn't assume any particular data model.__ One of the problems with OLAP cubes
  was that they required you to transform your data into a very strictly defined shape.
  Dictum strives to be more flexible. It will work with Star schema, Snowflake schema,
  just a bunch of entity tables and even just a production database (with some
  limitations of course).
- __It tries to do one job well.__ Dictum tries to keep a narrow scope, within reason.
  It is a tool that allows you to describe what your data _means_, which metrics there
  are and how you can slice them. Then it helps you query your data without thinking
  about non-business stuff. So, it is _not_ a data transformation tool. Things like
  calculating sequential order number per user or sessions are out of scope. You can
  calculate that with dbt and use the results for defining metrics.

We also believe in the ideas stated in the dbt
[Viewpoint](https://docs.getdbt.com/docs/about/viewpoint). Drag-and-drop interfaces are
good for quick throwaway work that doesn't require versioning or collaboration. When
you're building something that will reflect organizational knowledge, be modified by many
people and gradually evolved, you can't do better than plaintext. So, when you interact
with Dictum as a user, you use a web interface, but the data model itself is written
as a YAML configuration file (or files).
