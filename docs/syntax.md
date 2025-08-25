# JSONPath Syntax

Python JSONPath extends the [RFC 9535](https://datatracker.ietf.org/doc/html/rfc9535) specification with additional features and relaxed rules. If you need strict compliance with RFC 9535, set `strict=True` when calling [`findall()`](convenience.md#jsonpath.findall), [`finditer()`](convenience.md#jsonpath.finditer), etc., which enforces the standard without these extensions.

In this guide, we first outline the standard syntax (see the specification for the formal definition), and then describe the non-standard extensions and their semantics in detail.

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

### Root identifier

The root identifier, `$`, refers to the outermost node in the target document. This can be an object, an array, or a scalar value.

A query containing only the root identifier simply returns the entire input document.

**Example query**

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

### Name selector

A _name selector_ matches the value of an object member by its key. You can write it in either **shorthand notation** (`.thing`) or **bracket notation** (`['thing']` or `["thing"]`).

Dot notation can be used when the property name is a valid identifier. Bracket notation is required when the property name contains spaces, special characters, or starts with a number.

**Example query**

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

### Index selector

The index selector selects an element from an array by its index. Indices are zero-based and enclosed in brackets, `[0]`. If the index is negative, items are selected from the end of the array.

**Example query**

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

### Wildcard selector

The _wildcard selector_ matches all member values of an object or all elements in an array. It can be written as `.*` (shorthand notation) or `[*]` (bracket notation).

**Example query**

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

### Slice selector

The slice selector allows you to select a range of elements from an array. A start index, ending index and step size are all optional and separated by colons, `[start:end:step]`. Negative indices count from the end of the array, just like standard Python slicing.

**Example query**

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

### Filter selector

Filters allow you to remove nodes from a selection based on a Boolean expression, `[?expression]`. A filter expression evaluates each node in the context of either the root (`$`) or current (`@`) node.

When filtering a mapping-like object, `@` identifies the current member value. When filtering a sequence-like object, `@` identifies the current element.

Comparison operators include `==`, `!=`, `<`, `>`, `<=`, and `>=`. Logical operators `&&` (and) and `||` (or) can combine terms, and parentheses can be used to group expressions.

A filter expression on its own - without a comparison - is treated as an existence test.

**Example query**

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

So far we've seen shorthand notation (`.selector`) and segments with just one selector (`[selector]`). Here we cover the descendant segment and segments with multiple selectors.

### Segments with multiple selectors

A segment can include multiple selectors separated by commas and enclosed in square brackets (`[selector, selector, ...]`). Any valid selector (names, indices, slices, filters, or wildcards) can appear in the list.

**Example query**

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

### Descendant segment

The descendant segment (`..`) visits all object member values and array elements under the current object or array, applying the selector or selectors that follow to each visited node. It must be followed by a shorthand selector (names, wildcards, etc.) or a bracketed list of one or more selectors.

**Example query**

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

The selectors and identifiers described in this section are an extension to the RFC 9535 specification. They are enabled by default. Set `strict=True` when constructing a [`JSONPathEnvironment`](api.md#jsonpath.JSONPathEnvironment), calling [`findall()`](convenience.md#jsonpath.findall), [`finditer()`](convenience.md#jsonpath.finditer), etc. to disable all non-standard features.

Also note that when `strict=False`:

- The root identifier (`$`) is optional and paths starting with a dot (`.`) are OK. `.thing` is the same as `$.thing`, as is `thing` and `$["thing"]`.
- Leading and trailing whitespace is OK.
- Explicit comparisons to `undefined` (aka `missing`) are supported as well as implicit existence tests.

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

**_New in version 2.0.0_**

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

The pseudo root identifier (`^`) behaves like the standard root identifier (`$`), but conceptually wraps the target JSON document in a single-element array. This allows the root document itself to be conditionally selected by filters.

#### Syntax

```
jsonpath-query             = (root-identifier / pseudo-root-identifier) segments

root-identifier            = "$"
pseudo-root-identifier     = "^"
```

#### Examples

```json title="Example JSON data"
{ "a": { "b": 42 }, "n": 7 }
```

| Query                      | Result                         | Result Path | Comment                             |
| -------------------------- | ------------------------------ | ----------- | ----------------------------------- |
| `^[?@.a.b > 7]`            | `{ "a": { "b": 42 } }`         | `^[0]`      | Conditionally select the root value |
| `^[?@.a.v > value(^.*.n)]` | `{ "a": { "b": 42 }, "n": 7 }` | `^[0]`      | Embedded pseudo root query          |

### Filter context identifier

The filter context identifier (`_`) starts an embedded query, similar to the root identifier (`$`) and current node identifier (`@`), but targets JSON-like data passed as the `filter_context` argument to [`findall()`](api.md#jsonpath.JSONPath.findall) and [`finditer()`](api.md#jsonpath.JSONPath.finditer).

#### Syntax

```
current-node-identifier  = "@"
extra-context-identifier = "_"

filter-query        = rel-query / extra-context-query / jsonpath-query
rel-query           = current-node-identifier segments
extra-context-query = extra-context-identifier segments

singular-query      = rel-singular-query / abs-singular-query / extra-context-singular-query
rel-singular-query  = current-node-identifier singular-query-segments
abs-singular-query  = root-identifier singular-query-segments

extra-context-singular-query = extra-context-identifier singular-query-segments
```

#### Examples

```json title="Example JSON data"
{ "a": [{ "b": 42 }, { "b": 3 }] }
```

```json title="Extra JSON data"
{ "c": 42 }
```

| Query              | Result        | Result Path | Comment                                      |
| ------------------ | ------------- | ----------- | -------------------------------------------- |
| `$.a[?@.b == _.c]` | `{ "b": 42 }` | `$['a'][0]` | Comparison with extra context singular query |

## Non-standard operators

In addition to the operators described below, the standard _logical and_ operator (`&&`) is aliased as `and`, the standard _logical or_ operator (`||`) is aliased as `or`, and `null` is aliased as `nil` and `none`.

Also, `true`, `false`, `null` and their aliases can start with an upper case letter.

### Membership operators

The membership operators test whether one value occurs within another.

An infix expression using `contains` evaluates to true if the right-hand side is a member of the left-hand side, and false otherwise.

- If the left-hand side is an object and the right-hand side is a string, the result is true if the object has a member with that name.
- If the left-hand side is an array, the result is true if any element of the array is equal to the right-hand side.
- For scalars (strings, numbers, booleans, null), `contains` always evaluates to false.

The `in` operator is equivalent to `contains` with operands reversed. This makes `contains` and `in` symmetric, so either form may be used depending on which reads more naturally in context.

A list literal is a comma separated list of JSONPath expression literals. List should appear on the left-hand side of `contains` or the right-hand side of `in`.

#### Syntax

```
basic-expr          = paren-expr /
                      comparison-expr /
                      membership-expr /
                      test-expr

membership-expr     = comparable S membership-op S comparable

membership-operator = "contains" / "in"

membership-operand  = literal /
                      singular-query / ; singular query value
                      function-expr /  ; ValueType
                      list-literal

list-literal        = "[" S literal *(S "," S literal) S "]"
```

#### Examples

```json title="Example JSON data"
{
  "x": [{ "a": ["foo", "bar"] }, { "a": ["bar"] }],
  "y": [{ "a": { "foo": "bar" } }, { "a": { "bar": "baz" } }],
  "z": [{ "a": "foo" }, { "a": "bar" }]
}
```

| Query                                 | Result                  | Result Path | Comment                              |
| ------------------------------------- | ----------------------- | ----------- | ------------------------------------ |
| `$.x[?@.a contains 'foo']`            | `{"a": ["foo", "bar"]}` | `$['x'][0]` | Array contains string literal        |
| `$.y[?@.a contains 'foo']`            | `{"a": ["foo", "bar"]}` | `$['y'][0]` | Object contains string literal       |
| `$.x[?'foo' in @.a]`                  | `{"a": ["foo", "bar"]}` | `$['x'][0]` | String literal in array              |
| `$.y[?'foo' in @.a]`                  | `{"a": ["foo", "bar"]}` | `$['y'][0]` | String literal in object             |
| `$.z[?(['bar', 'baz'] contains @.a)]` | `{"a": "bar"}`          | `$['z'][1]` | List literal contains embedded query |

### Regex operator

`=~` is an infix operator that matches the left-hand side with a regular expression literal on the right-hand side. Regular expression literals use a syntax similar to that found in JavaScript, where the pattern to match is surrounded by slashes, `/pattern/`, optionally followed by flags, `/pattern/flags`.

```
$..products[?(@.description =~ /.*trainers/i)]
```

### Union and intersection operators

The union or concatenation operator, `|`, combines matches from two or more paths.

The intersection operator, `&`, produces matches that are common to both left and right paths.

Note that compound queries are not allowed inside filter expressions.

#### Syntax

```
jsonpath-query          = root-identifier segments

compound-jsonpath-query = jsonpath-query compound-op jsonpath-query

compound-op             = "|" /
                          "&"
```

#### Examples

```text
$..products.*.price | $.price_cap
```

```text
$.categories[?(@.name == 'footwear')].products.* & $.categories[?(@.name == 'headwear')].products.*
```
