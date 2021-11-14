# jsonschema-lint

Linter for JSON Schema instances.

## Installation

This project is not currently packaged and so must be installed manually.

Clone the project with the following command:
```
git clone https://github.com/jacksmith15/jsonschema-lint.git
```

## Usage

The linter is invoked on the command line:

```
$ jsonschema-lint
```

### Selecting instances

By default, the linter will attempt to lint every file matching extension under the currect directory. This means every `.json` file, plus every `.yaml`/`.yml` file if [PyYAML] is installed. A file will only be linted if a matching schema can be detected (see [below](#-selecting-schemas)).

You can override this behaviour by passing arguments to the linter, e.g.

```
$ jsonschema-lint **/*.avsc
```

### Schema resolution

There are three ways schemas can be selected for a given instance. In order of priority:

1. If provided, the `--schema` option will be used to validate all target instances.
1. A matching rule in a `.jsonschema-lint` file, in the instance directory or its parents (see below).
1. If the `--schema-store` flag is provided, then matching rules from [Schema Store](https://www.schemastore.org/json/) will be used.


#### `.jsonschema-lint` files

`.jsonschema-lint` files follow similar logic to `.gitignore` and [Github `CODEOWNERS` files](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners), in that they apply to all files under their directory tree.

Each line in a `.jsonschema-lint` file is a rule, matching a filepath pattern to a particular schema. For example:

```
**/.circleci/config.yml  https://json.schemastore.org/circleciconfig.json  yaml
```

There are three parts to each rule, separated by whitespace. These are:

- the pattern/glob, in this case matching any files named `config.yml` in a directory named `.circleci`
- the location of the schema. This can be a remote URL, or a path on the local filesystem. If this is a relative path, it is resolved relative to the `.jsonschema-lint` file.
- (optional) the expected file format of any instances. If this is omitted, the linter will attempt to detect the correct type from the file extension. If it cannot be detected, both will be attempted.


## Development

Install dependencies:

```shell
pyenv shell 3.9.4  # Or other 3.9.x
pre-commit install  # Configure commit hooks
poetry install  # Install Python dependencies
```

Run tests:

```shell
poetry run inv verify
```

# License

This project is distributed under the MIT license.


[PyYAML]: https://pypi.org/project/PyYAML/
