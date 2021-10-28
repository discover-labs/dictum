# Getting started

Hyperplane was designed for an easy start. You can create a minimal data model in just
a dozen of lines of code and then build from there.

## Install Hyperplane

Just install with `pip`:

```bash
--8<-- "snippets/getting_started/install.sh"
```

## Create a minimal project

You specify the data model for your project in one or more YAML files. You can start with
a single-file approach and split your project into multiple files as it grows.

Create a `tutorial` directory and add a `project.yml` file:

```{ .yaml title=project.yml }
--8<-- "snippets/getting_started/minimal_project.yml"
```

Yes, that's right, the only thing required for a project is a name. You can also add an
optional `description` field.

## Create the example database

Hyperplane ships with a really simple example SQLite database unimaginatively called
`example`.  It's used in tests, and here we'll use it to showcase all the important
features.

```sh
--8<-- "snippets/getting_started/example_database.sh"
```

## Create the profiles file

In addition to the data model, Hyperplane needs to know where your data is stored.
The connection information is stored separately in a file that's usually called
`profiles.yml`.

You can have several profiles and switch between them. One use case for several profiles
is when you have a separate environment for developing and testing you data transformations
and want to see how your metrics work with the next version of your data warehouse.

Here's a `profiles.yml` file that Hyperplane will use to connect to the `example.db`
database that we just created:

```{ .yaml title=profiles.yml }
--8<-- "snippets/getting_started/example_profiles.yml"
```

The first value is `default`. This must be a name of one of the profiles specified below.
This is the profile that will be use by default, when no other profile is explicitly
requested.

Next, we define our profiles. All profiles must have a `type`. This is the name of either
a [built-in backend](../reference/backends.md) or a backend provided by a [plugin](../reference/plugins.md).

Currently Hyperplane ships with two backends: `sqlite` and `postgres`. Many other backends
are supported by official plugins.

Each backend type requires it's own set of parameters, which can be looked up in the
documentation. `sqlite` backend only needs one parameter, called `database`, which is
a path to the database file we want to use.

## Start the server

To start the server, run this command:

```sh
--8<-- "snippets/getting_started/start_server.sh"
```

In a couple of seconds the local Hyperplane server will start and you can go to
[http://localhost:8000](http://localhost:8000). Right now our data model is empty, so
we don't see anything there yet.
