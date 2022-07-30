# Metric

!!! info
    Before reading this, make sure you understand what a
    [Measure](measure.md) is.

A metric is a calculation over measures. In the simplest and most
common case, a metric is just a reference to a single measure.

By default, metric definitions are stored in separate files in the
`metrics` directory of your project. The filename without the
extension is treated like the internal identifier for the metric.
Metrics can reference each other with this identifier, which allows
you to gradually build more and more metrics derived from other
metrics.


## Schema

!!! info
    This schema is only for metrics that are defined as
    a calculation over one or more measures.
    For metrics that are also measures, see
    [Measure](measure.md#defining-measures-as-metrics).

```yaml
name: |
    string, required
    Human-readable descriptive display name for a metric

description: |
    string, optional
    A longer description for documentation purposes.

expr: |
    string expression, required
    An aggregate expression, e.g. sum(amount).
    A non-aggregate expression will result in an error.
    For details, see Expression language reference.

type: |
    float | int | date | datetime | bool | str, defaults to float
    The data type of the calculation. Because most measures are
    numerical in nature, defaults to float.

format: |
    string or dict, optional
    Formatting information (see Formatting).

missing: |
    whatever type is specified in the type field, optional
    If a query returns a missing value (NULL) in some slice, it will
    be replaced with this value.
```


## Example

```yaml
# metrics/visit_to_order_converion.yml
name: Visit -> Order Conversion
expr: $orders / $unique_visitors
format: percent
```
