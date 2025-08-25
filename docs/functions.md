# Filter Functions

A filter function is a named function that can be called as part of a [filter selector](syntax.md#filter-selector). Here we describe built in filters. You can [define your own function extensions](advanced.md#function-extensions) too.

## `count()`

```text
count(obj: object) -> Optional[int]
```

Return the number of items in _obj_. If the object does not respond to Python's `len()` function, `None` is returned.

```
$.categories[?count(@.products.*) >= 2]
```

## `isinstance()`

**_New in version 0.6.0_**

```text
isinstance(obj: object, t: str) -> bool
```

Return `True` if the type of _obj_ matches _t_. This function allows _t_ to be one of several aliases for the real Python "type". Some of these aliases follow JavaScript/JSON semantics.

| type                  | aliases                              |
| --------------------- | ------------------------------------ |
| UNDEFINED             | "undefined", "missing"               |
| None                  | "null", "nil", "None", "none"        |
| str                   | "str", "string"                      |
| Sequence (array-like) | "array", "list", "sequence", "tuple" |
| Mapping (dict-like)   | "object", "dict", "mapping"          |
| bool                  | "bool", "boolean"                    |
| int                   | "number", "int"                      |
| float                 | "number", "float"                    |

For example :

```
$.categories[?isinstance(@.length, 'number')]
```

And `is()` is an alias for `isinstance()`:

```
$.categories[?is(@.length, 'number')]
```

## `keys()`

**_New in version 2.0.0_**

```
keys(value: object) -> Tuple[str, ...] | Nothing
```

Return a list of keys from an object/mapping. If `value` does not have a `keys()` method, the special _Nothing_ value is returned.

!!! note

    `keys()` is not registered with the default JSONPath environment. The [keys selector](syntax.md#keys-selector) and [keys filter selector](syntax.md#keys-filter-selector) are usually the better choice when strict compliance with the specification is not needed.

    You can register `keys()` with your JSONPath environment like this:

    ```python
    from jsonpath import JSONPathEnvironment
    from jsonpath import function_extensions

    env = JSONPathEnvironment()
    env.function_extensions["keys"] = function_extensions.Keys()
    ```

```
$.some[?'thing' in keys(@)]
```

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

## `startswith()`

**_New in version 2.0.0_**

```
startswith(value: str, prefix: str) -> bool
```

Return `True` if `value` starts with `prefix`. If `value` or `prefix` are not strings, `False` is returned.

```
$[?startswith(@, 'ab')]
```

## `typeof()`

**_New in version 0.6.0_**

```text
typeof(obj: object) -> str
```

Return the type of _obj_ as a string. The strings returned from this function use JavaScript/JSON terminology like "string", "array" and "object", much like the result of JavaScript's `typeof` operator.

```
$.categories[?typeof(@.length) == 'number']
```

`type()` is and alias for `typeof()`.

`jsonpath.function_extensions.TypeOf` takes a `single_number_type` argument, which controls the behavior of `typeof()` when given and int or float. By default, `single_number_type` is `True` and `"number"` is returned. Register a new instance of `TypeOf` with a `JSONPathEnvironment` with `single_number_type` set to `False` and `"int"` and `"float"` will be returned when given integers and floats, respectively.

| instance              | type string                                            |
| --------------------- | ------------------------------------------------------ |
| UNDEFINED             | "undefined"                                            |
| None                  | "null"                                                 |
| str                   | "string"                                               |
| Sequence (array-like) | "array"                                                |
| Mapping (dict-like)   | "object"                                               |
| bool                  | "boolean"                                              |
| int                   | "number" or "int" if `single_number_type` is `False`   |
| float                 | "number" or "float" if `single_number_type` is `False` |

## `value()`

```
value(nodes: object) -> object | undefined
```

Return the first value from _nodes_ resulting from a JSONPath query, if there is only one node, or `undefined` otherwise.

```text
$..products[?value(@.price) == 9]
```
