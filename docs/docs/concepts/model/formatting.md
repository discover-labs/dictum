# Formatting

Definitions of calculations ([Measures](measure.md), [Dimensions](dimension.md) and
[Metrics](metric.md)) can contain information about how they should be formatted. This
information is used by Dictum to figure out how to display query results in Jupyter,
both as tables and [Altair](#) visualizations.

!!! info
    Formatting is [locale-dependent](../project.md#projectyml) and is supported by the
    great [Babel](https://babel.pocoo.org/) library. If you want to get into more
    details of format specification, be sure to read the documentation.


## Default formats for data types

If no formatting is specified, Dictum will use default values for the `type` of the
particular calculation.

`int` and `float` will be given a [short](#short-formats) `number` format.

`date` and `datetime` values will be given the corresponding format kind.


## Short formats

Format for a calculation is specified under the `format` key. The value can be a string
or a dictionary. For dictionary form, see
[full format specification](#full-format-specification) below.

In simple cases, a format can be specified as a string. Valid values are:

- `number` — format a numeric value as a plain number, e.g. `1,223`.
- `decimal` — same as `number`
- `percent` — format a numeric value as percentage, e.g. `4.82%`.
- `currency` — format a numeric value as currency, e.g. `$1.60`. Which currency is used
    is determined by the [default project currency](../project.md#projectyml).
- `date` — format a date value as a date, determined by project locale's default date
    format.
- `datetime` — format a datetime value as a datetime, determined by project locale's
    default datetime format.
- `string` — no formatting is applied.


## Full format specification

```yaml
kind: |
    number | decimal | percent | currency | date | datetime, required

pattern: |
    string, optional

skeleton: |
    string, optional
    Only valid for `date` and `datetime` format kinds.

currency: |
    string, optional
    Only valid for the `currency` kind. A 3-letter currency code,
    e.g. `USD`, `RUB`, `JPY`.
```

### Pattern documentation

Depending on the kind, the pattern will be interpreted as a date, datetime or number
Babel pattern.

- [Patterns for dates and datetimes](https://babel.pocoo.org/en/latest/dates.html#date-fields)
- [Patterns for numbers, currencies and percentanges](https://babel.pocoo.org/en/latest/numbers.html#pattern-syntax)
