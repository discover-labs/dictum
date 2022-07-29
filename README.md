<p align="center">
<img src="docs/docs/assets/dictum-logo-text.png" width="200" style="margin: 1em">
</p>

Dictum is a general-purpose __metrics engine__ written in Python.
It allows your organization to have a __shared__, __version-controlled__ and
__well-documented__ understanding of what the important metrics are and
how they are computed from the source data.

In addition to that, it empowers your team to expore the data without
thinking about distracting implementation details.

<p align="center">
<img src="docs/docs/assets/demo.gif" width="600">
</p>

Dictum supports a simple, __SQL-like expression language__ for defining
metrics and __automatic multi-hop joins__ to quickly slice and dice the data
without writing repetitive boilerplate SQL by hand. In Dictum, all calculations
are __reusable__, meaning that if you defined a metric once, you can then use
it to define other metrics.


## A structured way to describe your metrics

```yaml
# metrics/revenue.yml
name: Revenue
description: Sum of all order amounts excluding bonus currency spending.
table: orders
expr: sum(amount - coalesce(bonus_spent, 0))
format:
  kind: currency
  currency: USD
```

Dictum __Data Model__ is a single source of truth about
the _meaning_ and _structure_ of your data. It describes your metrics, dimensions =
and table relationships.

The model is a collection of YAML files that is supposed to be version-controlled and
shared across your analytics team. This allows your team to govern metric definitions
systematically, making your analysis consistent and repeatable.


## Interactive analytics in Jupyter

```py
from dictum import Project

project = Project("/path/to/project")
project.select("revenue").by("date.month").where("order_amount > 100")
```

After describing your existing metrics, you can query your data model in
every analyst's favourite tool for data analysis: [Jupyter](https://jupyter.org).

Build beautiful visualizations using [Altair](https://altair-viz.github.io/) or retrieve
data for analysis in Pandas. The engine uses flexible and expressive query idioms and
supports table calculations, filtering, top-K queries and more.
