# Getting Started

Dictum was designed for an easy start. You can create a minimal data model in just
a dozen of lines of code and then build from there.


## Install Dictum

Just install with `pip`:

```bash
--8<-- "snippets/getting_started/install.sh"
```


## Just query

Most of the time when developing your data model you will test queries interactively as
you go via Python. A good place to do this is a Jupyter Notebook, but you can use any
other tool.

If you'd like to just read the guide and run some queries on the example project, you
can do this:

```py
--8<-- "snippets/getting_started/load_example.py"
```

If you'd like to follow along writing the data model config yourself, read further,
otherwise skip the rest of this page.


## Clone the example template

You can clone the tutorial projects' empty template to follow along with this command:

```sh
git clone https://github.com/rad-data-labs/dictum-example-template tutorial
```

### `project.yml` file

There's a `project.yml` file in the cloned directory. It is the entry point of your data
model. You can write your whole model there or split it into multiple files, but this
file is what Dictum will read first.

```{ .yaml title=project.yml }
--8<-- "snippets/getting_started/minimal_project.yml"
```

The only thing required for a project is a name. You can also add an optional
`description` field.

### `profiles.yml` file

In addition to the data model, Dictum needs to know where your data is stored.
The connection information is stored separately in a file that's usually called
`profiles.yml`.

You can have several profiles and switch between them. One use case for several profiles
is when you have a separate environment for developing and testing you data transformations
and want to see how your metrics work with the next version of your data warehouse.

Here's a `profiles.yml` file that Dictum will use to connect to the `example.db`
database stored in the same directory:

```{ .yaml title=profiles.yml }
--8<-- "snippets/getting_started/example_profiles.yml"
```

The first value is `default`. This must be a name of one of the profiles specified below.
This is the profile that will be use by default, when no other profile is explicitly
requested.

Next, we define our profiles. All profiles must have a `type`. This is the name of either
a [built-in backend](../reference/backends.md) or a backend provided by a
[plugin](../reference/plugins.md).

Currently Dictum ships with two backends: `sqlite` and `postgres`. Many other backends
are supported by official plugins.

Each backend type requires it's own set of parameters, which can be looked up in the
documentation. `sqlite` backend only needs one parameter, called `database`, which is
a path to the database file we want to use.

### Instantiate a Project

You can interact with you project by calling methods of an instance of `Project` class.
The `Project` needs to know where to look for the data model and profiles definition.
There are several ways to specify them.

Dictum will know where to look for the data model definition by reading the `path`
argument.

- if `path` is ommited, it will read `project.yml` file in the current working directory
- if `path` is specified and it's a directory, it will read `project.yml` file in that directory
- if `path` is a file, it will expect that the data model definition is in that file

Profiles file path can be specified by `profiles` argument:

- if `profiles` is ommited, Dictum will look for a `profiles.yml` file in the same directory where it found the data model file
- if `profiles` is specified, it must be a path to the profiles file

By default Dictum will use the default profile specified in `profiles.yml`. To use a
different profile, pass the `profile` argument.

If you're using Jupyter and you created your notebook file in the directory that we cloned
earlier, you can just instantiate the `Project` without arguments:

```py
from dictum import Project

tutorial = Project()
```

Here are several more examples of different combinations of arguments:

```py
from dictum import Project

# look for project.yml and profiles.yml in current working directory
tutorial = Project()

# look for project.yml and profiles.yml in /path/to/example/ directory
tutorial = Project(path="/path/to/example/")

# read the data model from /path/to/example/custom_project_name.yml file
# read the profiles from /path/to/example/profiles.yml
tutorial = Project(path="/path/to/example/custom_project_name.yml")

# read the data model from /path/to/example/project.yml
# read the profiles from /path/to/profiles.yml
tutorial = Project(path="/path/to/example/", profiles="/path/to/profiles.yml")

# read the data model from /path/to/example/project.yml
# read the profiles from /path/to/example/profiles.yml
# use the "staging" profiles instead of the specified default profile
tutorial = Project(path="/path/to/example/", profile="staging")
```
