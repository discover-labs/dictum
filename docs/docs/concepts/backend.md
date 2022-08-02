# Backend

A backend is reponsible for translating abstract Dictum computations into actual queries.
Before you can use Dictum, you have to set up at least one backend in the `profiles.yml`
file.

## Installing backends

Backends are installed together with Dictum by installing `dictum` package's extras.

| Backend                                        | Installation command           | Configuration              |
| ---------------------------------------------- | ------------------------------ | -------------------------- |
| [Postgres](https://www.postgresql.org/)        | `pip install dictum[postgres]` | [postgres](#postgres)      |
| [Vertica](https://www.vertica.com/)            | `pip install dictum[vertica]`  | [vertica](#vertica)        |

## Profiles

Each backend specification is called a "profile". There's one default profile, the one
Dictum will connect to if no other profile is specified when you initialize the `Project`
object.

Let's look at an example.

```yaml
# profiles.yml
default_profile: prod
profiles:
  prod:
    type: postgres
    parameters:
      host: pg.example.com
      port: 5432
      database: example
      user: example
      password: {{ env.EXAMPLE_PASSWORD }}
      default_schema: example
  dev:
    type: postgres
    parameters:
      host: pg.example.com
      port: 5432
      database: example
      user: example
      password: {{ env.EXAMPLE_PASSWORD }}
      default_schema: example_test
```

If you have a development environment in another schema where you made some changes and
want to test them, you can create a `Project` object pointing to the corresponding profile:

```python
from dictum import Project

dev = Project("/path/to/project", profile="dev")
```

Each backend type has its own set of parameters listed in the documentation below.

## Jinja templating

`profiles.yml` is run through Jinja templating engine before being used. It means that
you don't have to put any sensitive information (like database passwords) into version
control.

The only available context object is `env` which holds your environment variables. Dictum
expects them to be present, but if they're not found, the user will be prompted to enter
them when a project is created.

## Officially supported backends

Although anyone can create a backend plugin, some backends are officially supported. It
means that when a new version of Dictum (or a supported backend) is rolled out, we run
all the automated tests with the new version to make sure that everything works as
expected.

Backends are supposed to work together with Dictum within a minor version. So, Dictum
versions `0.2.x` are compatible with `dictum-backend-postgres` versions `0.2.x`

### SQLite (built-in)

This backend is shipped with Dictum.

!!! info
    Since SQLite doesn't support `full outer join`, all computations after the initial
    aggregations is done locally with Pandas.

Type: `sqlite`

Parameters:

- `database` — path to database file, e.g. `/path/to/chinook.sqlite`.

SQLite table sources are defined as a string table name.

### Postgres

Type: `postgres`

Parameters:

- `host` — Postgresql host, defaults to `localhost`
- `port` - defaults to `5432`, must be `int`
  If you want to get the port from `env`, use `int` Jinja filter:
  `port: {{ env.POSTGRES_PORT | int }}`
- `database` — Postgresql database name
- `user` — Postgresql user for authentication
- `password` — Postgresql user password for authentication
- `pool_size` — defaults to `5`. SQLAlchemy pool size for executing concurrent queries,
  which is required when Dictum can't resolve a query to a single SQL query.
- `default_schema` — default schema to use when no schema is specified.
  When defining Dictum tables, you can specify the source as `source: my_table`. If
  `default_schema` is present, Dictum will look for the table in that schema.

Postgresql table sources can be defined in two ways:

- as a string table name, e.g. `source: my_table`. In this case Dictum will look for the
  table in the `default_schema`, and if it's not provided, will rely on the database's
  `search_path` to figure out which schema to use.
- as a dictionary, e.g.
  ```yaml
  source:
    schema: my_schema
    table: my_table
  ```
  In this case, Dictum will use the schema specified in the table source config.
  `

### Vertica

Type: `vertica`

Parameters:

- `host` — Vertica host address, defaults to `localhost`
- `port` - Port to connect to, defaults to `5433`
  If you want to get the port from `env`, use `int` Jinja filter:
  `port: {{ env.POSTGRES_PORT | int }}`
- `database` — cluster database name
- `user` — user name for authenticaion
- `password` password for authentication
- `pool_size` — defaults to `5`. SQLAlchemy pool size for executing concurrent queries,
  which is required when Dictum can't resolve a query to a single SQL query.
- `default_schema` — default schema to use when no schema is specified.
  When defining Dictum tables, you can specify the source as `source: my_table`. If
  `default_schema` is present, Dictum will look for the table in that schema.
