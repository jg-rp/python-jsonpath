# Filter Functions

A filter function is a named function that can be called as part of a [filter selector](syntax.md#filters-expression) expression. Here we describe the standard, built-in filters. You can [define your own function extensions](advanced.md#function-extensions) too.

## `count()`

```text
count(obj: object) -> Optional[int]
```

Return the number of items in _obj_. If the object does not respond to Python's `len()` function, `None` is returned.

```
$.categories[?count(@.products.*) >= 2]
```

!!! warning
As of Python JSONPath version 0.5.0, `count` is an alias for `length`. This might change in the future.

## `length()`

```text
length(obj: object) -> Optional[int]
```

Return the number of items in the input object. If the object does not respond to Python's `len()` function, `None` is returned.

```
$.categories[?length(@) > 1]
```

## `match()`

```text
match(obj: object, pattern: str) -> bool
```

Return `True` if _obj_ is a string and is a full match to the regex _pattern_.

```text
$..products[?match(@.title, ".+ainers.+")]
```

If _pattern_ is a string literal, it will be compiled at compile time, and raise a `JSONPathTypeError` at compile time if it's invalid.

If _pattern_ is a query and the result is not a valid regex, `False` is returned.

## `search()`

```text
search(obj: object, pattern: str) -> bool
```

Return `True` if _obj_ is a string and it contains the regexp _pattern_.

```text
$..products[?search(@.title, "ainers")]
```

If _pattern_ is a string literal, it will be compiled at compile time, and raise a `JSONPathTypeError` at compile time if it's invalid.

If _pattern_ is a query and the result is not a valid regex, `False` is returned.

## `value()`

```
value(nodes: object) -> object | undefined
```

Return the first value from _nodes_ resulting from a JSONPath query, if there is only one node, or `undefined` otherwise.

```text
$..products[?value(@.price) == 9]
```
