# Project

Dictum project is a collection of YAML files stored in a specially
structured directory.  To generate scaffolding for a new project,
run `dictum new` in the CLI.

## Default project structure

In addition to the `project.yml` file, a project directory contains
definitions of [Tables](model/table.md) with [Measures](model/measure.md)
and [Dimensions](model/dimension.md) and of course [Metrics](model/metric.md).

The default directory structure is as follows:

```
├── metrics
│   ├── metric1.yml
│   ├── ...
│   ├── subdirectory
│   │   ├── metric2.yml
├── profiles.yml
├── project.yml
├── tables
│   ├── table1.yml
└── unions.yml
```

- `metrics` — This directory stores [metrics](model/metric.md),
    one file per metric.
    Files can be arranged in arbitrary subdirectories, but in that
    case metric filenames must be globally unique (metrics can
    reference each other by that name).
- `tables` — Stores information about [tables](model/table.md),
    organized the same way as metrics.
- `unions.yml` — This file contains definitions of
    [unions](model/dimension.md#unions)
- `profiles.yml` — This file tells Dictum how to connect to the data
    source, which database driver to use etc (see [Backend](model/backend.md))


## project.yml

The heart of a Dictum project is `project.yml` file. It must be present
in the root of a project directory. It contains general information about
your project: project name, how Dictum should display numbers and dates,
where Dictum can find definitions of metrics etc.

```yaml
name: |
    string, required
    A project name.
description: |
    string, optional
    Project description.
locale: |
    string, defaults to "en_US"
    A locale to use for this project. This will affect how
    numbers, dates and currency values are displayed.
currency: |
    string, defaults to "USD"
    Default currency to use for metrics with currency format.
    You can specify a different currency in the metric formatting options.

tables_path: |
    string, defaults to "tables"
    Path to the definition of tables. If a directory, table
    definitions are assumed to be stored in separate .yml
    files with filenames (without the extension) corresponding
    to table IDs.
    If a .yml file, the root object must be a dictionary with keys corresponsing to table IDs.
metrics_path: |
    string, defaults to "metrics"
    Like tables, but for metrics.
unions_path: |
    string, defaults to "unions.yml"
    Like tables, but for dimension unions.
profiles_path: |
    string, defaults to "profiles.yml"
    Like tables, but for backend profiles.

```
