# Python JSONPath

[![PyPI - Version](https://img.shields.io/pypi/v/python-jsonpath.svg)](https://pypi.org/project/python-jsonpath)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/python-jsonpath.svg)](https://pypi.org/project/python-jsonpath)

---

**Table of Contents**

- [Install](#install)
- [API](#api)
- [Syntax](#syntax)
- [License](#license)

A flexible JSONPath engine for Python.

JSONPath is a mini language for extracting objects from data formatted in JavaScript Object Notation, or equivalent Python objects like dictionaries, and lists.

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

```console
pip install -u python-jsonpath
```

or

```console
pipenv install python-jsonpath
```

## API

### jsonpath.findall

`findall(path: str, data: Sequence | Mapping) -> list[object]`

Find all objects in `data` matching the given JSONPath `path`. If data is a string, it will be loaded using `json.loads()` and the default `JSONDecoder`.

Returns a list of matched objects, or an empty list if there were not matches.

### jsonpath.finditer

`finditer(path: str, data: Sequence | Mapping) -> iterable[JSONPathMatch]`

Return an iterator yielding a `JSONPathMatch` instance for each match of the `path` in the given `data`. If data is a string, it will be loaded using `json.loads()` and the default `JSONDecoder`.

### jsonpath.compile

`compile(path: str) -> JSONPath | CompoundJSONPath`

Prepare a path for repeated matching against different data. `jsonpath.findall()` and `jsonpath.finditer()` are convenience functions that call `compile()` for you.

`JSONPath` and `CompoundJSONPath` both have `findall()` and `finditer()` methods that behave the same as `jsonpath.findall()` and `jsonpath.finditer()`, just without taking a path string argument.

### async

`findall_async()` and `finditer_async` are async equivalents of `findall()` and `finditer()`. They are used by when integrating Python JSONPath with [Python Liquid](https://github.com/jg-rp/liquid) and use Python Liquid's [async protocol](https://jg-rp.github.io/liquid/introduction/async-support).

### Extra filter context

`findall()` and `finditer()` take an optional `filter_context` argument, being a mapping of strings to arbitrary data that can be referenced from a [filter expression](#filters-expression).

Use `#` to query extra filter data, similar to how one might use `@` or `$`.

## Syntax

Python JSONPath's default syntax is an opinionated combination of JSONPath features from existing, popular implementations, and much of the [IETF JSONPath draft](https://datatracker.ietf.org/doc/html/draft-ietf-jsonpath-base-11). If you're already familiar with JSONPath syntax, skip to [Notable differences](#notable-differences).

TODO: tree analogy / target document
TODO: use "node" terminology  
TODO: mention JSON and Python equivalency

### Root (`$`)

`$` refers to the first node in the target document, be it an object or an array. Unless referencing the root node from inside a filter expression, `$` is optional. The following two examples are equivalent.

```text
$.categories.*.name
```

```text
categories.*.name
```

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

### Array indices (`.0`, `[0]` or `[-1]`)

Select an item from an array by its index. Indices are zero-based and enclosed in brackets. If the index is negative, items are selected from the end of the array. Considering example data from the top of this page, the following examples are equivalent.

```text
$.categories[0]
```

```text
$.categories.0
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

Filters allow you to remove nodes from a selection using a Boolean expression. Within a filter, `@` refers to the current node and `$` refers to the root node in the target document. `@` and `$` can be used to select nodes as part of the expression.

```text
$..products.*[?(@.price < $.price_cap)]
```

Comparison operators include `==`, `!=`, `<`, `>`, `<=` and `>=`. Plus `<>` as an alias for `!=`.

`in` and `contains` are membership operators. `left in right` is equivalent to `right contains left`.

`&&` and `||` are logical operators, `and` and `or` work too.

`=~` matches the left value with a regular expression literal. Regular expressions use a similar syntax to that found in JavaScript, where the pattern to match is surrounded by slashes, optionally followed by flags.

```text
$..products.*[?(@.description =~ /.*trainers/i)]
```

### Union (`|`) and intersection (`&`)

TODO:

## Notable differences

This is a list of things that you might find in other JSONPath implementation that we don't support (yet).

- We don't support extension functions of the form `selector.func()`.
- We always return a list of matches from `jsonpath.findall()`, never a scalar value.
- We do not support arithmetic in filter expression.

And this is a list of areas where we deviate from the [IETF JSONPath draft](https://datatracker.ietf.org/doc/html/draft-ietf-jsonpath-base-11).

- We don't support extension functions of the form `func(path, ..)`.
- Whitespace is mostly insignificant unless inside quotes.
- The root token (default `$`) is optional.
- Paths starting with a dot (`.`) are OK. `.thing` is the same as `$.thing`, as is `thing`, `$[thing]` and `$["thing"]`.
- Nested filters are not supported.
- When a filter is applied to an object (mapping) value, we do not silently apply that filter to the object's values. See the "Existence of non-singular queries" example in the IETF JSONPath draft.
- `|` is a union operator, where matches from two or more JSONPaths are combined.
- `&` is an intersection operator, where we output matches that exist in two paths.

## License

`python-jsonpath` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
