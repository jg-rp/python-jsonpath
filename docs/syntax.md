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
$
```

```json title="data"
{
  "categories": [
    { "id": 1, "name": "fiction" },
    { "id": 2, "name": "non-fiction" }
  ]
}
```

```json title="results"
[
  {
    "categories": [
      { "id": 1, "name": "fiction" },
      { "id": 2, "name": "non-fiction" }
    ]
  }
]
```

### Name selector (`.thing` or `['thing']`)

A _name selector_ matches the value of an object member by its key. You can write it in either **shorthand notation** (`.thing`) or **bracket notation** (`['thing']`).

Dot notation can be used when the property name is a valid identifier. Bracket notation is required when the property name contains spaces, special characters, or starts with a number.

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

```json title="results"
["Moby Dick"]
```

### Index selector (`[0]` or `[-1]`)

Select an element from an array by its index. Indices are zero-based and enclosed in brackets. If the index is negative, items are selected from the end of the array.

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

```json title="results"
["fiction"]
```

### Wildcard selector (`.*` or `[*]`)

The _wildcard selector_ matches all member values of an object or all elements in an array. It can be written as `.*` (shorthand notation) or `[*]` (bracket notation).

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

```json title="results"
["fiction", "non-fiction"]
```

### Slice selector (`[start:end:step]`)

The slice selector allows you to select a range of elements from an array. You can specify a starting index, an ending index (exclusive), and an optional step to skip elements. Negative indices count from the end of the array, just like standard Python slicing.

#### Example query

```text
$.items[1:4:2]
```

```json title="data"
{
  "items": ["a", "b", "c", "d", "e", "f"]
}
```

```json title="results"
["b", "d"]
```

### Filter selector (`[?expression]`)

Filters allow you to remove nodes from a selection based on a Boolean expression. A filter expression evaluates each node in the context of either the root (`$`) or the current node (`@`).

When filtering a mapping-like object, `@` identifies the current member value. When filtering a sequence-like object, `@` identifies the current element.

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

```json title="results"
[
  { "name": "apple", "price": 5 },
  { "name": "banana", "price": 8 }
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

```json title="results"
[
  { "title": "Book A", "price": 10 },
  { "title": "Book C", "price": 8 }
]
```

### Descendant segment (`..`)

The descendant segment (`..`) visits all object member values and array elements under the current object or array, applying the selector or selectors that follow to each visited node. It must be followed by a shorthand selector (names, wildcards, etc.) or a bracketed list of one or more selectors.

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

```json title="results"
[10, 12, 19.95]
```

## Non-standard selectors and identifiers

The selectors and identifiers described in this section are an extension to RFC 9535. They are enabled by default. See [#strict-mode] for details on how to use JSONPath following RFC 9535 strictly.

### Key selector

**_New in version 2.0.0_**

The key selector, `.~name` or `[~'name']`, selects at most one name from an object member. It is syntactically similar to the standard [name selector](https://datatracker.ietf.org/doc/html/rfc9535#name-name-selector), with the addition of a tilde (`~`) prefix.

When applied to a JSON object, the key selector selects the _name_ from an object member, if that name exists, or nothing if it does not exist. This complements the standard name selector, which select the _value_ from a name/value pair.

When applied to an array or primitive value, the key selector selects nothing.

Key selector strings must follow the same processing semantics as name selector strings, as described in [section 2.3.2.1](https://datatracker.ietf.org/doc/html/rfc9535#section-2.3.1.2) of RFC 9535.

!!! info

    The key selector is introduced to facilitate valid normalized paths for nodes produced by the [keys selector](#keys-selector) and the [keys filter selector](#keys-filter-selector). I don't expect it will be of much use elsewhere.

#### Syntax

```
selector             = name-selector /
                       wildcard-selector /
                       slice-selector /
                       index-selector /
                       filter-selector /
                       key-selector /
                       keys-selector /
                       keys-filter-selector

key-selector         = "~" name-selector

child-segment        = bracketed-selection /
                       ("."
                        (wildcard-selector /
                         member-name-shorthand /
                         member-key-shorthand))

descendant-segment   = ".." (bracketed-selection /
                             wildcard-selector /
                             member-name-shorthand /
                             member-key-shorthand)

member-key-shorthand = "~" name-first *name-char
```

#### Examples

```json title="Example JSON document"
{
  "a": [{ "b": "x", "c": "z" }, { "b": "y" }]
}
```

| Query       | Result            | Result Paths                              | Comment                       |
| ----------- | ----------------- | ----------------------------------------- | ----------------------------- |
| `$.a[0].~c` | `"c"`             | `$['a'][0][~'c']`                         | Key of nested object          |
| `$.a[1].~c` |                   |                                           | Key does not exist            |
| `$..[~'b']` | `"b"` <br/> `"b"` | `$['a'][0][~'b']` <br/> `$['a'][1][~'b']` | Descendant, single quoted key |
| `$..[~"b"]` | `"b"` <br/> `"b"` | `$['a'][0][~'b']` <br/> `$['a'][1][~'b']` | Descendant, double quoted key |

### Keys selector

**_New in version 0.6.0_**

The keys selector, `~` or `[~]`, selects all names from an object’s name/value members. This complements the standard [wildcard selector](https://datatracker.ietf.org/doc/html/rfc9535#name-wildcard-selector), which selects all values from an object’s name/value pairs.

As with the wildcard selector, the order of nodes resulting from a keys selector is not stipulated.

When applied to an array or primitive value, the keys selector selects nothing.

The normalized path of a node selected using the keys selector uses [key selector](#key-selector) syntax.

#### Syntax

```
keys-selector       = "~"
```

#### Examples

```json title="Example JSON document"
{
  "a": [{ "b": "x", "c": "z" }, { "b": "y" }]
}
```

| Query          | Result                                    | Result Paths                                                                              | Comment                    |
| -------------- | ----------------------------------------- | ----------------------------------------------------------------------------------------- | -------------------------- |
| `$.a[0].~`     | `"b"` <br/> `"c"`                         | `$['a'][0][~'b']` <br/> `$['a'][0][~'c']`                                                 | Object keys                |
| `$.a.~`        |                                           |                                                                                           | Array keys                 |
| `$.a[0][~, ~]` | `"b"` <br/> `"c"` <br/> `"c"` <br/> `"b"` | `$['a'][0][~'b']` <br/> `$['a'][0][~'c']` <br/> `$['a'][0][~'c']` <br/> `$['a'][0][~'b']` | Non-deterministic ordering |
| `$..[~]`       | `"a"` <br/> `"b"` <br/> `"c"` <br/> `"b"` | `$[~'a']` <br/> `$['a'][0][~'b']` <br/> `$['a'][0][~'c']` <br/> `$['a'][1][~'b']`         | Descendant keys            |

### Keys filter selector

**_New in version 2.0.0_**

The keys filter selector selects names from an object’s name/value members. It is syntactically similar to the standard [filter selector](https://datatracker.ietf.org/doc/html/rfc9535#name-filter-selector), with the addition of a tilde (`~`) prefix.

```
~?<logical-expr>
```

Whereas the standard filter selector will produce a node for each _value_ from an object’s name/value members - when its expression evaluates to logical true - the keys filter selector produces a node for each _name_ in an object’s name/value members.

Logical expression syntax and semantics otherwise match that of the standard filter selector. `@` still refers to the current member value. See also the [current key identifier](#current-key-identifier).

When applied to an array or primitive value, the keys filter selector selects nothing.

The normalized path of a node selected using the keys filter selector uses [key selector](#key-selector) syntax.

#### Syntax

```
filter-selector     = "~?" S logical-expr
```

#### Examples

```json title="Example JSON document"
[{ "a": [1, 2, 3], "b": [4, 5] }, { "c": { "x": [1, 2] } }, { "d": [1, 2, 3] }]
```

| Query                  | Result            | Result Paths                    | Comment                          |
| ---------------------- | ----------------- | ------------------------------- | -------------------------------- |
| `$.*[~?length(@) > 2]` | `"a"` <br/> `"d"` | `$[0][~'a']` <br/> `$[2][~'d']` | Conditionally select object keys |
| `$.*[~?@.x]`           | `"c"`             | `$[1][~'c']`                    | Existence test                   |
| `$[~?(true == true)]`  |                   |                                 | Keys from an array               |

### Singular query selector

The singular query selector consist of an embedded absolute singular query, the result of which is used as an object member name or array element index.

If the embedded query resolves to a string or int value, at most one object member value or array element value is selected. Otherwise the singular query selector selects nothing.

#### Syntax

```
selector                = name-selector /
                          wildcard-selector /
                          slice-selector /
                          index-selector /
                          filter-selector /
                          singular-query-selector

singular-query-selector = abs-singular-query
```

#### Examples

```json
{
  "a": {
    "j": [1, 2, 3],
    "p": {
      "q": [4, 5, 6]
    }
  },
  "b": ["j", "p", "q"],
  "c d": {
    "x": {
      "y": 1
    }
  }
}
```

| Query                 | Result             | Result Path      | Comment                                                           |
| --------------------- | ------------------ | ---------------- | ----------------------------------------------------------------- |
| `$.a[$.b[1]]`         | `{"q": [4, 5, 6]}` | `$['a']['p']`    | Object name from embedded singular query                          |
| `$.a.j[$['c d'].x.y]` | `2`                | `$['a']['j'][1]` | Array index from embedded singular query                          |
| `$.a[$.b]`            |                    |                  | Embedded singular query does not resolve to a string or int value |

### Current key identifier

`#` is the _current key_ identifier. `#` will be the name of the current object member, or index of the current array element. This complements the current node identifier (`@`), which refers to a member value or array element, respectively.

It is a syntax error to follow the current key identifier with segments, as if it were a filter query.

When used as an argument to a function, the current key is of `ValueType`, and outside a function call it must be compared.

#### Syntax

```
comparable             = literal /
                         singular-query / ; singular query value
                         function-expr  / ; ValueType
                         current-key-identifier


function-argument      = literal /
                         filter-query / ; (includes singular-query)
                         logical-expr /
                         function-expr /
                         current-key-identifier

current-key-identifier = "#"
```

#### Examples

```json title="Example JSON document"
{ "abc": [1, 2, 3], "def": [4, 5], "abx": [6], "aby": [] }
```

| Query                                     | Result                | Result Path                       | Comment                     |
| ----------------------------------------- | --------------------- | --------------------------------- | --------------------------- |
| `$[?match(#, '^ab.*') && length(@) > 0 ]` | `[1,2,3]` <br/> `[6]` | `$['abc']` <br/> `$['abx']`       | Match on object names       |
| `$.abc[?(# >= 1)]`                        | `2` <br/> `3`         | `$['abc'][1]` <br/> `$['abc'][2]` | Compare current array index |

### Pseudo root identifier

**_New in version 0.11.0_**

The pseudo root identifier (`^`) behaves like the standard root identifier (`$`), but conceptually wraps the target JSON document in a single-element array. This allows the root document itself to be addressed by selectors such as filters, which normally only apply to elements within arrays.

#### Syntax

```
jsonpath-query             = (root-identifier / pseudo-root-identifier) segments

root-identifier            = "$"
pseudo-root-identifier     = "^"
```

#### Examples

TODO

### Filter context identifier

The filter context identifier (`_`) starts an embedded query, similar to the root identifier (`$`) and current node identifier (`@`), but targets JSON-like data passed as the `filter_context` argument to [`findall()`](api.md#jsonpath.JSONPath.findall) and [`finditer()`](api.md#jsonpath.JSONPath.finditer).

#### Syntax

TODO

#### Examples

TODO

## Non-standard operators

TODO

### Lists (`[1, 2, 10:20]`)

Select multiple indices, slices or properties using list notation (sometimes known as a "union" or "segment", we use "union" to mean something else).

```text
$..products.*.[title, price]
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
