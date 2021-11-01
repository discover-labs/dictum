# Organizing a Larger Project with Multiple Files

As your project grows, so does your config file. Most real-life projects contain dozens
of tables, which are hard to navigate between in a single file. Fortunately, Hyperplane
allows you to put each table's config into a separate file.


## Create `tables` folder

Hyperplane expects your table configs to be in YAML files inside `tables` folder, at the
same path as your `project.yml` file. This folder's expected name is controlled by
`tables_dir` option in your `project.yml`. The default is `tables`, but you can set it to
whatever you want.

You can organize your table files into nested subfolders. For example, in a dimensional
warehouse you might have `facts`, `dimensions` and `links`. Or you could organize them
by a business domain: `marketing`, `finance`, `product`.

```
root
├── project.yml
├── profiles.yml
└── tables
    ├── orders.yml
    ├── categories.yml
    ├── users.yml
    └── user_sessions.yml
```

!!! important
    Regardless of subfolder structure, table filenames must be unique — the part before
    the extension will become your table's ID.

    Hyperplane will give you an error if you have a duplicate table ID in your project.


##  Move your tables into separate files

Each table file is a single table config, so you'll have table keys `source`,
`primary_key`, `related`, `measures`, `dimensions` at the root level of the config.

```{ .yaml title="tables/users.yml" }
--8<-- "snippets/multiple_files/users.yml"
```
