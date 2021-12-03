# Transforms and Filters

```yaml
parameters:
  period:
    values: [year, quarter, month, week, day, hour]
    type: string
    default: week
  periods:
    type: number
    default: 30
    range: [10, 100]
    step: 5

tables:
  orders:
    source: orders
    primary_key: id
  dimensions:
    order_date:
      name: order date
      type: date
      expr: created_at
      defaults:
        transform: datetrunc(@period)
        filter: last(@periods, @period)
```

```py
(
    project.select("revenue")
    .parameters(
        period="month",
        periods=10,
    )
    .by("order_date")
)
```
