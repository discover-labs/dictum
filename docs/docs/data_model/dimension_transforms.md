# Default Transforms and Filters

Most of the calculations should be defined in your data model, but in some cases it's
better to have more flexibility at query time. Hyperplane allows users to define
additional transformations for dimensions when requesting them.


## Query defaults

Transforms are defined at query time, but you're reading about them in the data model
guide. That's because you can also define default transforms that can be later overriden
by a user.

Imagine if a user requests `Number of Orders` by `Order Amount` without any transform.
It will result in a huge and useless chunk of data, because order amounts can take any
value whatsoever. They probably want to see a distribution and it's good to give them
a sensible default to start from.

```{ .yaml hl_lines="11 12" }
--8<-- "snippets/dimension_transforms/query_defaults.yml"
```

!!! info
    Default transforms (and filters, which you'll learn about later) exist to protect
    users and are not enforced on the server-side. The client interacting with the API
    is free to use or ignore them. Hyperplane web interface automatically adds them
    when a dimension is added, but the users of GraphQL and Python APIs are expected to
    know what they're doing.
