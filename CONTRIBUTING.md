# Contributing to Python JSONPath

Hi. Your contributions and questions are always welcome. Feel free to ask questions, report bugs or request features on the [issue tracker](https://github.com/jg-rp/python-jsonpath/issues) or on [Github Discussions](https://github.com/jg-rp/python-jsonpath/discussions). Pull requests are welcome too.

**Table of contents**

- [Development](#development)
- [Documentation](#documentation)
- [Style Guides](#style-guides)

## Development

The [JSONPath Compliance Test Suite](https://github.com/jsonpath-standard/jsonpath-compliance-test-suite) and [JSONPath Normalized Path Test Suite](https://github.com/jg-rp/jsonpath-compliance-normalized-paths) are included in this repository as Git [submodules](https://git-scm.com/book/en/v2/Git-Tools-Submodules). Clone this project and initialize the submodules with something like:

```shell
$ git clone git@github.com:jg-rp/python-jsonpath.git
$ cd python-jsonpath
$ git submodule update --init
```

We use [hatch](https://hatch.pypa.io/latest/) to manage project dependencies and development environments.

Run tests with the _test_ script.

```shell
$ hatch run test
```

Lint with [ruff](https://beta.ruff.rs/docs/).

```shell
$ hatch run lint
```

Typecheck with [Mypy](https://mypy.readthedocs.io/en/stable/).

```shell
$ hatch run typing
```

Check coverage with pytest-cov.

```shell
$ hatch run cov
```

Or generate an HTML coverage report.

```shell
$ hatch run cov-html
```

Then open `htmlcov/index.html` in your browser.

## Documentation

Documentation is currently in the [README](https://github.com/jg-rp/python-jsonpath/blob/main/README.md) and project source code only.

## Style Guides

### Git Commit Messages

There are no hard rules for git commit messages, although you might like to indicate the type of commit by starting the message with `docs:`, `chore:`, `feat:`, `fix:` or `refactor:`, for example.

### Python Style

We use [Ruff](https://docs.astral.sh/ruff/) to lint and format all Python files.

Ruff is configured to:

- follow [Black](https://github.com/psf/black), with its default configuration.
- expect [Google style docstrings](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html).
- enforce Python imports according to [isort](https://pycqa.github.io/isort/) with `force-single-line = true`.
