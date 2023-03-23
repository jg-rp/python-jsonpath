# python-jsonpath

[![PyPI - Version](https://img.shields.io/pypi/v/python-jsonpath.svg)](https://pypi.org/project/python-jsonpath)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/python-jsonpath.svg)](https://pypi.org/project/python-jsonpath)

---

**Table of Contents**

- [About](#about)
- [Syntax](#syntax)
- [License](#license)

## About

Another JSONPath implementation for Python. Specifically one that is strictly read-only, has no external dependencies, is fully type-checked and has an async interface compatible with [Python Liquid's async protocol](https://jg-rp.github.io/liquid/introduction/async-support).

This project is in the early stages of development. If you stubble across it, don't try and use it yet. More to follow.

## Syntax

TODO:

### Array indexing and slicing

TODO:

`a[0]` or `a[-1]`

`a[:]` or `a[1:-1]` or `a[1:]` or `a[:2]`

### Things worthy of note

- We don't support arbitrary extension functions, only filters.
- Whitespace is mostly insignificant unless inside quotes.
- The root token (default `$`) is optional.
- Paths starting with a dot (`.`) are OK. `.thing` is the same as `$.thing`, as is `thing`, `$[thing]` and `$["thing"]`.
- Any bracket notation elements can be preceded with a dot (`.`). `$.thing.["other"]` is equivalent to `$.thing["other"]`.
- `|` is a union operator, where matches from two or more JSONPaths are combined.
- `&` is an intersection operator, where matches must exist in a left and right path.
- Our "lists" are sometimes called "unions". Lists can contain slices, indexes and/or properties.

### BNF

`jsonpath.bnf` is a bnf-like description of the JSONPath syntax accepted by this package.

The BNF syntax used here is the one preferred by the [SLY project](https://sly.readthedocs.io/en/latest/sly.html#writing-a-parser). Note that this project does not use SLY. We've chosen to write our own lexer and parser.

- `[ thing ]` means zero or one
- `{ thing }` means zero or more
- Upper case names are symbols defined elsewhere.

The specifics of `ROOT`, `IDENTIFIER` and `FILTER_EXPRESSION` are configurable options. Hence the reason for excluding their definitions from `jsonpath.bnf`.

## License

`python-jsonpath` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
