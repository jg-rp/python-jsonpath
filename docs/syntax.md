# JSONPath Syntax

Python JSONPath's default syntax is an opinionated combination of JSONPath features from existing, popular implementations and [RFC 9535](https://datatracker.ietf.org/doc/html/rfc9535). If you're already familiar with JSONPath syntax, skip to [notable differences](#notable-differences).

Imagine a JSON document as a tree structure, where each object (mapping) and array can contain more objects, arrays and scalar values. Every object, array and scalar value is a node in the tree, and the outermost object or array is the "root" node.

For our purposes, a JSON "document" could be a file containing valid JSON data, a Python string containing valid JSON data, or a Python `Object` made up of dictionaries (or any [Mapping](https://docs.python.org/3/library/collections.abc.html#collections-abstract-base-classes)), lists (or any [Sequence](https://docs.python.org/3/library/collections.abc.html#collections-abstract-base-classes)), strings, etc.

We chain _selectors_ together to retrieve nodes from the target document. Each selector operates on the nodes matched by preceding selectors. What follows is a description of those selectors.

## Selectors

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

By default, `or`, `and`, `in`, `true`, `True`, `false`, `False`, `nil`, `Nil`, `null`, `Null`, `none`, `None`, `contains`, `undefined`, and `missing` are considered _reserved words_. In some cases you will need to use quoted property/name selector syntax if you're selecting a name that matches any of these words exactly. For example, `["and"]`.

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

### Keys (`.~` or `[~]`)

**_New in version 0.6.0_**

Select keys/properties from an object using `~`.

```text
$.categories.~
```

```text
$.categories[~]
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

### Filters (`[?EXPRESSION]`)

Filters allow you to remove nodes from a selection using a Boolean expression. A _filter query_ is a JSONPath query nested within a filter expression. Every filter query must start with the root identifier (`$`), the current node identifier (`@`) or the [filter context](advanced.md#filter-variables) identifier (`_`).

```text
$..products[?(@.price < $.price_cap)]
```

```text
$..products[?@.price < $.price_cap]
```

When filtering a mapping-like object, `#` references the current key/property and `@` references the current value associated with `#`. When filtering a sequence-like object, `@` references the current item and `#` will hold the item's index in the sequence.

Comparison operators include `==`, `!=`, `<`, `>`, `<=` and `>=`. Plus `<>` as an alias for `!=`.

`in` and `contains` are membership operators. `left in right` is equivalent to `right contains left`.

`&&` and `||` are logical operators and terms can be grouped with parentheses. `and` and `or` work too.

`=~` matches the left value with a regular expression literal. Regular expressions use a syntax similar to that found in JavaScript, where the pattern to match is surrounded by slashes, optionally followed by flags.

```text
$..products[?(@.description =~ /.*trainers/i)]
```

A filter query on its own - one that is not part of a comparison expression - is an existence test. We also support comparing a filter query to the special `undefined` keyword. These two example are equivalent.

```text
$..products[?!@.sale_price]
```

```text
$..products[?@.sale_price == undefined]
```

Filter expressions can call predefined [function extensions](functions.md) too.

```text
$.categories[?count(@.products.*) >= 2]
```

### Fake root (`^`)

**_New in version 0.11.0_**

This non-standard "fake root" identifier behaves like the standard root identifier (`$`), but wraps the target JSON document in a single-element array, so as to make it selectable with a filter selector.

```text
^[?length(categories) > 0]
```

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
