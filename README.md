# Python JSONPath

[![PyPI - Version](https://img.shields.io/pypi/v/python-jsonpath.svg?style=flat-square)](https://pypi.org/project/python-jsonpath)
[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/jg-rp/python-jsonpath/tests.yaml?branch=main&label=tests&style=flat-square)](https://github.com/jg-rp/python-jsonpath/actions)
[![PyPI - License](https://img.shields.io/pypi/l/python-jsonpath?style=flat-square)](https://github.com/jg-rp/python-jsonpath/blob/main/LICENSE.txt)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/python-jsonpath.svg?style=flat-square)](https://pypi.org/project/python-jsonpath)

---

**Table of Contents**

- [Install](#install)
- [API](#api)
- [Syntax](#syntax)
- [License](#license)

A flexible JSONPath engine for Python.

JSONPath is a mini language for extracting objects from data formatted in JavaScript Object Notation, or equivalent Python objects, like dictionaries and lists.

```python
import jsonpath

data = {
    "categories": [
        {
            "name": "footwear",
            "products": [
                {
                    "title": "Trainers",
                    "description": "Fashionable trainers.",
                    "price": 89.99,
                },
                {
                    "title": "Barefoot Trainers",
                    "description": "Running trainers.",
                    "price": 130.00,
                },
            ],
        },
        {
            "name": "headwear",
            "products": [
                {
                    "title": "Cap",
                    "description": "Baseball cap",
                    "price": 15.00,
                },
                {
                    "title": "Beanie",
                    "description": "Winter running hat.",
                    "price": 9.00,
                },
            ],
        },
    ],
    "price_cap": 10,
}

products = jsonpath.findall("$..products.*", data)
print(products)
```

## Install

Install Python JSONPath using [Pipenv](https://pipenv.pypa.io/en/latest/):

```console
pipenv install -u python-jsonpath
```

or [pip](https://pip.pypa.io/en/stable/getting-started/):

```console
pip install python-jsonpath
```

or [pipx](https://pypa.github.io/pipx/)

```console
pipx install python-jsonpath
```

## API

### jsonpath.findall

`findall(path: str, data: Sequence | Mapping) -> list[object]`

Find all objects in `data` matching the given JSONPath `path`. If data is a string, it will be loaded using `json.loads()` and the default `JSONDecoder`.

Returns a list of matched objects, or an empty list if there were no matches.

### jsonpath.finditer

`finditer(path: str, data: Sequence | Mapping) -> iterable[JSONPathMatch]`

Return an iterator yielding a `JSONPathMatch` instance for each match of the `path` in the given `data`. If data is a string, it will be loaded using `json.loads()` and the default `JSONDecoder`.

### jsonpath.compile

`compile(path: str) -> JSONPath | CompoundJSONPath`

Prepare a path for repeated matching against different data. `jsonpath.findall()` and `jsonpath.finditer()` are convenience functions that call `compile()` for you.

`JSONPath` and `CompoundJSONPath` both have `findall()` and `finditer()` methods that behave the same as `jsonpath.findall()` and `jsonpath.finditer()`, just without the path argument.

### async

`findall_async()` and `finditer_async()` are async equivalents of `findall()` and `finditer()`. They are used when integrating Python JSONPath with [Python Liquid](https://github.com/jg-rp/liquid) and use Python Liquid's [async protocol](https://jg-rp.github.io/liquid/introduction/async-support).

### Extra filter context

`findall()` and `finditer()` take an optional `filter_context` argument, being a mapping of strings to arbitrary data that can be referenced from a [filter expression](#filters-expression).

Use `#` to query extra filter data, similar to how one might use `@` or `$`.

## Syntax

Python JSONPath's default syntax is an opinionated combination of JSONPath features from existing, popular implementations, and much of the [IETF JSONPath draft](https://datatracker.ietf.org/doc/html/draft-ietf-jsonpath-base-11). If you're already familiar with JSONPath syntax, skip to [notable differences](#notable-differences).

Imagine a JSON document as a tree structure, where each object (mapping) and array can contain more objects (mappings), arrays and scalar values. Every object (mapping), array and scalar value is a node in the tree, and the outermost object (mapping) or array is the "root" node.

For our purposes, a JSON "document" could be a file containing valid JSON data, a Python string containing valid JSON data, or a Python `Object` made up of dictionaries (or any [Mapping](https://docs.python.org/3/library/collections.abc.html#collections-abstract-base-classes)), lists (or any [Sequence](https://docs.python.org/3/library/collections.abc.html#collections-abstract-base-classes)), strings, etc.

We chain _selectors_ together to retrieve nodes from the target document. Each selector operates on the nodes matched by preceding selectors.

### Root (`$`)

`$` refers to the first node in the target document, be it an object or an array. Unless referencing the root node from inside a filter expression, `$` is optional. The following two examples are equivalent.

```text
$.categories.*.name
```

```text
categories.*.name
```

An empty path or a path containing just the root (`$`) selector returns the input data in its entirety.

### Properties (`.thing`, `[thing]` or `['thing']`)

Select nodes by property/key name using dot notation (`.something`) or bracket notation (`[something]`). If a target property/key contains reserved characters, it must use bracket notation and be enclosed in quotes (`['thing']`).

A dot in front of bracket notation is OK, but unnecessary. The following examples are equivalent.

```text
$.categories[0].name
```

```text
$.categories[0][name]
```

```text
$.categories[0]['name']
```

### Array indices (`[0]` or `[-1]`)

Select an item from an array by its index. Indices are zero-based and enclosed in brackets. If the index is negative, items are selected from the end of the array. Considering example data from the top of this page, the following examples are equivalent.

```text
$.categories[0]
```

```text
$.categories[-1]
```

### Wildcard (`.*` or `[*]`)

Select all elements from an array or all values from an object using `*`. These two examples are equivalent.

```text
$.categories[0].products.*
```

```text
$.categories[0].products[*]
```

### Slices (`[0:-1]` or `[-1:0:-1]`)

Select a range of elements from an array using slice notation. The start index, stop index and step are all optional. These examples are equivalent.

```text
$.categories[0:]
```

```text
$.categories[0:-1:]
```

```text
$.categories[0:-1:1]
```

```text
$.categories[::]
```

### Lists (`[1, 2, 10:20]`)

Select multiple indices, slices or properties using list notation (sometimes known as a "union" or "segment", we use "union" to mean something else).

```text
$..products.*.[title, price]
```

### Recursive descent (`..`)

The `..` selector visits every node beneath the current selection. If a property selector, using dot notation, follows `..`, the dot is optional. These two examples are equivalent.

```text
$..title
```

```text
$...title
```

### Filters (`[?(EXPRESSION)]`)

Filters allow you to remove nodes from a selection using a Boolean expression. Within a filter, `@` refers to the current node and `$` refers to the root node in the target document. `@` and `$` can be used to select nodes as part of the expression. Since version 0.3.0, the parentheses are optional, as per the IETF JSONPath draft. These two examples are equivalent.

```text
$..products[?(@.price < $.price_cap)]
```

```text
$..products[?@.price < $.price_cap]
```

Comparison operators include `==`, `!=`, `<`, `>`, `<=` and `>=`. Plus `<>` as an alias for `!=`.

`in` and `contains` are membership operators. `left in right` is equivalent to `right contains left`.

`&&` and `||` are logical operators, `and` and `or` work too.

`=~` matches the left value with a regular expression literal. Regular expressions use a syntax similar to that found in JavaScript, where the pattern to match is surrounded by slashes, optionally followed by flags.

```text
$..products[?(@.description =~ /.*trainers/i)]
```

Filters can use [function extensions](#function-extensions) too.

### Union (`|`) and intersection (`&`)

Union (`|`) and intersection (`&`) are similar to Python's set operations, but we don't dedupe the matches (matches will often contain unhashable objects).

The `|` operator combines matches from two or more paths. This example selects a single list of all prices, plus the price cap as the last element.

```text
$..products.*.price | $.price_cap
```

The `&` operator produces matches that are common to both left and right paths. This example would select the list of products that are common to both the "footwear" and "headwear" categories.

```text
$.categories[?(@.name == 'footwear')].products.* & $.categories[?(@.name == 'headwear')].products.*
```

Note that `|` and `&` are not allowed inside filter expressions.

## Function extensions

TODO:

## Notable differences

This is a list of things that you might find in other JSONPath implementation that we don't support (yet).

- We don't support extension functions of the form `selector.func()`.
- We always return a list of matches from `jsonpath.findall()`, never a scalar value.
- We do not support arithmetic in filter expression.
- Python JSONPath is strictly read only. There are no update "selectors", although a Python API for working with `JSONPathMatch`s may well be added in the future.

And this is a list of areas where we deviate from the [IETF JSONPath draft](https://datatracker.ietf.org/doc/html/draft-ietf-jsonpath-base-11).

- We don't yet follow all "non-singular query" rules when evaluating a filter comparison.
- We don't yet force the result of some filter functions to be compared.
- Whitespace is mostly insignificant unless inside quotes.
- The root token (default `$`) is optional.
- Paths starting with a dot (`.`) are OK. `.thing` is the same as `$.thing`, as is `thing`, `$[thing]` and `$["thing"]`.

And this is a list of features that are uncommon or unique to Python JSONPath.

- `|` is a union operator, where matches from two or more JSONPaths are combined. This is not part of the Python API, but built-in to the JSONPath syntax.
- `&` is an intersection operator, where we exclude matches that don't exist in both left and right paths. This is not part of the Python API, but built-in to the JSONPath syntax.
- `#` is a filter context selector. With usage similar to `$` and `@`, `#` exposes arbitrary data from the `filter_context` argument to `findall()` and `finditer()`.

## License

`python-jsonpath` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
