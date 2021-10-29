# Introduction

Hyperplane is a semantic layer for your data. It translates questions like:

- How many signups per week do we have?
- What is the Average Revenue per User, by countries of Europe?
- What is the most profitable user cohort after 30 days from the first order?

into the language of data: tables, relationships and joins, aggregations and filters.

Business users, domain experts and data analysts can ask these kinds of questions in a
web interface, Hyperplane will translate them into database queries and present the
results.

In addition to that, it can be used without the web server directly from Python to
query data interactively and build data visualizations.

In different times this kind of tool was called different names:

- __OLAP cubes__. Expensive, proprietary and hard to develop, they were very popular in
  their time and are still widely used. Hyperplane is somewhat similar to ROLAP mode of
  operation: it doesn't store data, but generates queries that the database backend
  then executes.
- __Metric store__. Like a metric store, Hyperplane allows you to define how metrics
  are calculated and then view them. Unlike a metric store, it tries to make minimal
  assumptions about what your goal might be.

A very similar and certainly more mature tool is [Cube.js](https://cube.dev/). It is a
headless tool (so no web interface) that operates under the same model, but differs
in some design details.

## Where to start

Read the [Data model guide](data_model/getting_started.md).

## Design considerations

Hyperplane was designed with several things in mind. It's unopinionated in some things
and very opinionated in others.

- __It doesn't make assumptions about your data stack.__ We all love dbt. Really. But
  it's stange to assume that everyone uses it. Hyperplane will work regardless of upstream
  tools you're using to transform your data. People who use SSIS also deserve good tools.
- __It doesn't assume any particular data model.__ One of the problems with OLAP cubes
  was that they required you to transform your data into a very strictly defined shape.
  Hyperplane strives to be more flexible. It will work with Star schema, Snowflake schema,
  just a bunch of entity tables and even just a production database (with some
  limitations of course).
- __It tries to do one job well.__ Hyperplane tries to keep a narrow scope, within reason.
  It is a tool that allows you to describe what your data _means_, which metrics there
  are and how you can break them down. Then it helps you query your data without thinking
  about non-business stuff. So, it is _not_ a data transformation tool. Things like
  calculating sequential order number per user or sessions are out of scope. You can
  calculate that with dbt and use the results for defining metrics.

We also believe in the ideas stated in the dbt
[Viewpoint](https://docs.getdbt.com/docs/about/viewpoint). Drag-and-drop interfaces are
good for quick throwaway work that doesn't require versioning or collaboration. When
you're building something that will reflect organizational knowledge, be modified by many
people and gradually evolved, you can't do better than plaintext. So, when you interact
with Hyperplane as a user, you use a web interface, but the data model itself is written
as a YAML configuration file (or files).
