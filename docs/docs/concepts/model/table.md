# Table

Tables are the most fundamental part of a Dictum model. When you're starting
with a new project, it's recommended to begin by defining your tables.

By default Dictum looks for table definitions inside the `tables`
folder directory in your project. Each table should be stored in a
separate file. This file's name without the extension will be interpreted
as this table's internal identifier. You can use it to refer to this table
from other tables when defining relationships.

## Schema

```yaml
description: |
    string, optional
    Table description (for documentation purposes).

source: |
    string or dict, required
    Tells the backend where to look for this table.
    For SQL backends, if this is a string, the backend will
    look for the table in the default schema. If you want to
    specify a non-default schema, use a dictionary, e.g.
    source:
      table: mytable
      schema: myschema

primary_key: |
    string, optional
    A column that will be considered a primary key for this table.
    If you don't specify this, you will have to explicitly specify
    the join key every time you reference this table as related to
    some other table.

related: |
    dict, optional
    Information about related tables with foreign keys. This information
    will be used to automatically construct joins. Each relationship
    has an key-identifier which is used for referencing this related
    table in an expression (see example below).

measures: |
    dict, optional
    Information about measures for this table (see Measures).

dimensions: |
    dict, optional
    Information about dimensions for this table (see Dimensions).

filters: |
    a list of expressions, optional
    A list of filters to apply to this table. This should be used
    when you need to get a number of logical tables from a single
    physical table or otherwise apply filters globally to all
    measures defined for this table.
```

## Example

```yaml
# tables/invoice_items.yml

description: |
  Contains a row for each item (product) in an invoice. This is the
  most detailed information about orders.

source: invoice_items

related:
  invoices: InvoiceId -> invoices.InvoiceId
  tracks: TrackId -> tracks  # the primary key defined for tracks table will be used as a join key

measures:
  revenue:
    metric: true
    name: Revenue
    expr: sum(UnitPrice * Quantity)
    format: currency
    date: sale_date

dimensions:
  sale_date:
    name: Sale Date
    expr: invoices.InvoiceDate  # the invoices table will be automatically joined when this dimension is requested
    type: date
```
