# JSONPath Syntax

By default, Python JSONPath extends the RFC 9535 specification with a few additional features and relaxed rules, making it more forgiving in everyday use. If you need strict compliance with RFC 9535, you can enable strict mode, which enforces the standard without these extensions. In this guide, we first outline the standard syntax (see the specification for the formal definition), and then describe the non-standard extensions and their semantics in detail.

## JSONPath Terminology

Think of a JSON document as a tree, objects (mappings) and arrays can contain other objects, arrays, or scalar values. Each of these (object, array, or scalar) is a _node_ in the tree. The outermost object or array is called the _root_ node.

In this guide, a JSON "document" may refer to:

- A file containing valid JSON text
- A Python string containing valid JSON text
- A Python object composed of dictionaries (or any [Mapping](https://docs.python.org/3/library/collections.abc.html#collections-abstract-base-classes)), lists (or any [Sequence](https://docs.python.org/3/library/collections.abc.html#collections-abstract-base-classes)), strings, numbers, booleans, or `None`

A JSONPath expression (aka "query") is made up of a sequence of **segments**. Each segment contains one or more **selectors**:

- A _segment_ corresponds to a step in the path from one set of nodes to the next.
- A _selector_ describes how to choose nodes within that step (for example, by name, by index, or by wildcard).

What follows is a description of these selectors, starting with the standard ones defined in [RFC 9535](https://www.rfc-editor.org/rfc/rfc9535).

## Standard selectors and identifiers

### Root identifier (`$`)

The root identifier, `$`, refers to the outermost node in the target document. This can be an object, an array, or a scalar value.

A query containing only the root identifier simply returns the entire input document.

#### Example query

```
$.categories.*.name
```

```json title="data"
{
  "categories": [
    { "id": 1, "name": "fiction" },
    { "id": 2, "name": "non-fiction" }
  ]
}
```

```text title="results"
["fiction", "non-fiction"]
```

### Name selector (`.thing` or `['thing']`)

A _name selector_ matches the value of an object member by its key. You can write it in either **dot notation** (`.thing`) or **bracket notation** (`['thing']`).

Dot notation is concise and preferred when the property name is a valid identifier. Bracket notation is required when the property name contains spaces, special characters, or starts with a number.

#### Example query

```text
$.book.title
```

```json title="data"
{
  "book": {
    "title": "Moby Dick",
    "author": "Herman Melville"
  }
}
```

```text title="results"
["Moby Dick"]
```

### Index selector (`[0]` or `[-1]`)

Select an item from an array by its index. Indices are zero-based and enclosed in brackets. If the index is negative, items are selected from the end of the array.

#### Example query

```text
$.categories[0].name
```

```json title="data"
{
  "categories": [
    { "id": 1, "name": "fiction" },
    { "id": 2, "name": "non-fiction" }
  ]
}
```

```text title="results"
["fiction"]
```

### Wildcard selector (`.*` or `[*]`)

A _wildcard selector_ matches all member values of an object or all items in an array. It can be written as `.*` (dot notation) or `[*]` (bracket notation).

#### Example query

```text
$.categories[*].name
```

```json title="data"
{
  "categories": [
    { "id": 1, "name": "fiction" },
    { "id": 2, "name": "non-fiction" }
  ]
}
```

```text title="results"
["fiction", "non-fiction"]
```

### Slice selector (`[start:end:step]`)

The slice selector allows you to select a range of items from an array. You can specify a starting index, an ending index (exclusive), and an optional step to skip elements. Negative indices count from the end of the array, just like standard Python slicing.

#### Example query

```text
$.items[1:4:2]
```

```json title="data"
{
  "items": ["a", "b", "c", "d", "e", "f"]
}
```

```text title="results"
["b", "d"]
```

### Filter selector (`[?expression]`)

Filters allow you to remove nodes from a selection based on a Boolean expression. A filter expression evaluates each node in the context of either the root (`$`) or the current node (`@`).

When filtering a mapping-like object, `@` identifies the current member value. When filtering a sequence-like object, `@` identifies the current item.

Comparison operators include `==`, `!=`, `<`, `>`, `<=`, and `>=`. Logical operators `&&` (and) and `||` (or) can combine terms, and parentheses can be used to group expressions.

A filter expression on its own - without a comparison - is treated as an existence test.

#### Example query

```text
$..products[?(@.price < $.price_cap)]
```

```json title="data"
{
  "price_cap": 10,
  "products": [
    { "name": "apple", "price": 5 },
    { "name": "orange", "price": 12 },
    { "name": "banana", "price": 8 }
  ]
}
```

```text title="results"
[
  {"name": "apple", "price": 5},
  {"name": "banana", "price": 8}
]
```

Filter expressions can also call predefined [function extensions](functions.md).

## More on segments

So far we've seen shorthand notation and segments with just one selector. Here we cover the descendant segment and segments with multiple selectors.

### Segments with multiple selectors

A segment can include multiple selectors separated by commas and enclosed in square brackets (`[...]`). Any valid selector (names, indices, slices, filters, or wildcards) can appear in the list.

#### Example query

```text
$.store.book[0,2]
```

```json title="data"
{
  "store": {
    "book": [
      { "title": "Book A", "price": 10 },
      { "title": "Book B", "price": 12 },
      { "title": "Book C", "price": 8 }
    ]
  }
}
```

```text title="results"
[
  {"title": "Book A", "price": 10},
  {"title": "Book C", "price": 8}
]
```

### Descendant segment (`..`)

The descendant segment (`..`) visits all object member values and array elements under the current object or array, applying the selector or selectors that follow to each visited node. It can be followed by any valid shorthand selector (names, wildcards, etc.) or a bracketed list of one or more selectors, making it highly flexible for querying nested structures.

#### Example query

```text
$..price
```

```json title="data"
{
  "store": {
    "book": [
      { "title": "Book A", "price": 10 },
      { "title": "Book B", "price": 12 }
    ],
    "bicycle": { "color": "red", "price": 19.95 }
  }
}
```

```text title="results"
[10, 12, 19.95]
```

## Non-standard selectors and identifiers

TODO:

### Keys (`.~` or `[~]`)

**_New in version 0.6.0_**

Select keys/properties from an object using `~`.

```text
$.categories.~
```

```text
$.categories[~]
```

### Lists (`[1, 2, 10:20]`)

Select multiple indices, slices or properties using list notation (sometimes known as a "union" or "segment", we use "union" to mean something else).

```text
$..products.*.[title, price]
```

### Fake root (`^`)

**_New in version 0.11.0_**

This non-standard "fake root" identifier behaves like the standard root identifier (`$`), but wraps the target JSON document in a single-element array, so as to make it selectable with a filter selector.

```text
^[?length(categories) > 0]
```

## Non-standard operators

TODO

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

## Notable differences

This is a list of things that you might find in other JSONPath implementation that we don't support (yet).

- We don't support extension functions of the form `selector.func()`.
- We always return a list of matches from `jsonpath.findall()`, never a scalar value.
- We do not support arithmetic in filter expression.
- We don't allow dotted array indices. An array index must be surrounded by square brackets.
- Python JSONPath is strictly read only. There are no update "selectors", but we do provide methods for converting `JSONPathMatch` instances to `JSONPointer`s, and a `JSONPatch` builder API for modifying JSON-like data structures using said pointers.

And this is a list of areas where we deviate from [RFC 9535](https://datatracker.ietf.org/doc/html/rfc9535). See [jsonpath-rfc9535](https://github.com/jg-rp/python-jsonpath-rfc9535) for an alternative implementation of JSONPath that does not deviate from RFC 9535.

- The root token (default `$`) is optional and paths starting with a dot (`.`) are OK. `.thing` is the same as `$.thing`, as is `thing`, `$[thing]` and `$["thing"]`.
- The built-in `match()` and `search()` filter functions use Python's standard library `re` module, which, at least, doesn't support Unicode properties. We might add an implementation of `match()` and `search()` using the third party [regex](https://pypi.org/project/regex/) package in the future.
- We don't check `match()` and `search()` regex arguments against RFC 9485. Any valid Python pattern is allowed.
- We don't require property names to be quoted inside a bracketed selection, unless the name contains reserved characters.
- We don't require the recursive descent segment to have a selector. `$..` is equivalent to `$..*`.
- We support explicit comparisons to `undefined` as well as implicit existence tests.
- Float literals without a fractional digit are OK or leading digit. `1.` is equivalent to `1.0`.
- We treat literals (such as `true` and `false`) as valid "basic" expressions. For example, `$[?true || false]`, without an existence test or comparison either side of logical _or_, does not raise a syntax error.
- By default, `and` is equivalent to `&&` and `or` is equivalent to `||`.
- `none` and `nil` are aliases for `null`.
- `null` (and its aliases), `true` and `false` can start with an upper or lower case letter.
- We don't treat some invalid `\u` escape sequences in quoted name selectors and string literals as an error. We match the behavior of the JSON decoder in Python's standard library, which is less strict than RFC 9535.

And this is a list of features that are uncommon or unique to Python JSONPath.

- We support membership operators `in` and `contains`, plus list/array literals.
- `|` is a union operator, where matches from two or more JSONPaths are combined. This is not part of the Python API, but built-in to the JSONPath syntax.
- `&` is an intersection operator, where we exclude matches that don't exist in both left and right paths. This is not part of the Python API, but built-in to the JSONPath syntax.
- `#` is the current key/property or index identifier when filtering a mapping or sequence.
- `_` is a filter context identifier. With usage similar to `$` and `@`, `_` exposes arbitrary data from the `filter_context` argument to `findall()` and `finditer()`.
- `~` is a "keys" or "properties" selector.
- `^` is a "fake root" identifier. It is equivalent to `$`, but wraps the target JSON document in a single-element array, so the root value can be conditionally selected with a filter selector.
- `=~` is the the regex match operator, matching a value to a JavaScript-style regex literal.
