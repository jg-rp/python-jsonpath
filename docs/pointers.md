# JSON Pointers

**_New in version 0.8.0_**

JSON Pointer ([RFC 6901](https://datatracker.ietf.org/doc/html/rfc6901)) is a string syntax for targeting a single value (JSON object, array, or scalar) within a JSON document. Unlike a JSONPath expression, which can yield multiple values, a JSON Pointer resolves to **at most one value**.

JSON Pointers are a fundamental component of JSON Patch ([RFC 6902](https://datatracker.ietf.org/doc/html/rfc6902)), where each patch operation must have at least one pointer identifying the target location to modify.

??? note "Extensions to RFC 6901"

    We have extended RFC 6901 to support:

    - Interoperability with the JSONPath [keys selector](syntax.md#keys-or) (`~`)
    - A special non-standard syntax for targeting **keys or indices themselves**, used in conjunction with [Relative JSON Pointer](#torel)

    **Keys Selector Compatibility**

    The JSONPath **keys selector** (`.~` or `[~]`) allows expressions to target the *keys* of an object, rather than their associated values. To maintain compatibility when translating between JSONPath and JSON Pointer, our implementation includes special handling for this selector.

    While standard JSON Pointers always refer to values, we ensure that paths derived from expressions like `$.categories.~` can be represented in our pointer system. This is especially important when converting from JSONPath to JSON Pointer or when evaluating expressions that mix value and key access.

    **Key/Index Pointers (`#<key or index>`)**

    This non-standard pointer form represents **keys or indices themselves**, not the values they map to. Examples:

    - `#foo` points to the object key `"foo"` (not the value at `"foo"`)
    - `#0` points to the index `0` of an array (not the value at that index)

    This syntax is introduced to support the full capabilities of [Relative JSON Pointer](#torel), which allows references to both values and the *keys or indices* that identify them. To ensure that any `RelativeJSONPointer` can be losslessly converted into a `JSONPointer`, we use the `#<key or index>` form to represent these special cases.

    #### Example

    ```python
    from jsonpath import RelativeJSONPointer

    rjp = RelativeJSONPointer("1#")
    print(repr(rjp.to("/items/0/name")))  # JSONPointer('/items/#0')
    ```

## `resolve(data)`

Resolve this pointer against _data_. _data_ can be a file-like object or string containing JSON formatted data, or a Python [`Mapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping) or [`Sequence`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Sequence), like a dictionary or list.

```python
from jsonpath import JSONPointer

example_data = {"foo": {"bar": [1, 2, 3]}}
pointer = JSONPointer("/foo/bar/0")

print(pointer.resolve(example_data))  # 1
```

## `resolve_parent(data)`

Resolve this pointer against _data_, return the object and its parent as a `(parent, object)` tuple.

If _object_ does not exist in _data_ but _parent_ does, `(parent, UNDEFINED)` will be returned. Where `jsonpath.pointer.UNDEFINED` indicates the lack of a value.

If this pointer points to the JSON document root, parent will be `None`.

```python
from jsonpath import JSONPointer

example_data = {"foo": {"bar": [1, 2, 3]}}

pointer = JSONPointer("/foo/bar/0")
print(pointer.resolve_parent(example_data))  # ([1, 2, 3], 1)

# 'thing' does not exist
pointer = JSONPointer("/foo/thing")
print(pointer.resolve_parent(example_data))  # ({'bar': [1, 2, 3]}, <jsonpath.pointer._Undefined object at 0x7f0c7cf77040>)

pointer = JSONPointer("")
print(pointer.resolve_parent(example_data))  # (None, {'foo': {'bar': [1, 2, 3]}})
```

## `exists(data)`

**_New in version 0.9.0_**

Return _True_ if this pointer can be resolved against _data_, or _False_ otherwise. Note that `JSONPointer.resolve()` can return legitimate falsy values that form part of the target JSON document. This method will return `True` if a falsy value is found.

```python
from jsonpath import JSONPointer

example_data = {"foo": {"bar": [1, 2, 3]}, "baz": False}

pointer = JSONPointer("/foo/bar/0")
print(pointer.exists(example_data))  # True

pointer = JSONPointer("/foo/bar/9")
print(pointer.exists(example_data))  # False

pointer = JSONPointer("/baz")
print(pointer.exists(example_data))  # True
```

## `join(*parts)`

**_New in version 0.9.0_**

Join this pointer with _parts_. Each part is expected to be a JSON Pointer string, possibly without a leading slash. If a part does have a leading slash, the previous pointer is ignored and a new `JSONPointer` is created, and processing of remaining parts continues.

`join()` is equivalent to using the slash (`/`) operator for each argument.

```python
from jsonpath import JSONPointer

pointer = JSONPointer("/foo/bar")
print(pointer)  # /foo/bar
print(pointer.join("baz"))  # /foo/bar/baz
print(pointer.join("baz", "0"))  # /foo/bar/baz/0
```

## `parent()`

**_New in version 0.9.0_**

Return this pointer's parent as a new `JSONPointer`. If this pointer points to the document root, _self_ is returned.

```python
from jsonpath import JSONPointer

pointer = JSONPointer("/foo/bar")
print(pointer)  # /foo/bar
print(pointer.parent())  # /foo
```

## `is_relative_to(pointer)`

Return _True_ if this pointer points to a child of the argument pointer, which must be a `JSONPointer` instance.

```python
from jsonpath import JSONPointer

pointer = JSONPointer("/foo/bar")

another_pointer = JSONPointer("/foo/bar/0")
print(another_pointer.is_relative_to(pointer))  # True

another_pointer = JSONPointer("/foo/baz")
print(another_pointer.is_relative_to(pointer))  # False
```

## `to(rel)`

**_New in version 0.9.0_**

Return a new `JSONPointer` relative to this pointer. _rel_ should be a [`RelativeJSONPointer`](api.md#jsonpath.RelativeJSONPointer) instance or a string following [Relative JSON Pointer](https://www.ietf.org/id/draft-hha-relative-json-pointer-00.html) syntax.

```python
from jsonpath import JSONPointer

data = {"foo": {"bar": [1, 2, 3], "baz": [4, 5, 6]}}
pointer = JSONPointer("/foo/bar/2")

print(pointer.resolve(data))  # 3
print(pointer.to("0-1").resolve(data))  # 2
print(pointer.to("2/baz/2").resolve(data))  # 6
```

A `RelativeJSONPointer` can be instantiated for repeated application to multiple different pointers.

```python
from jsonpath import JSONPointer
from jsonpath import RelativeJSONPointer

data = {"foo": {"bar": [1, 2, 3], "baz": [4, 5, 6], "some": "thing"}}

some_pointer = JSONPointer("/foo/bar/0")
another_pointer = JSONPointer("/foo/baz/2")
rel = RelativeJSONPointer("2/some")

print(rel.to(some_pointer).resolve(data))  # thing
print(rel.to(another_pointer).resolve(data))  # thing
```

## Slash Operator

**_New in version 0.9.0_**

The slash operator allows you to create pointers that are children of an existing pointer.

```python
from jsonpath import JSONPointer

pointer = JSONPointer("/users")
child_pointer = pointer / "score" / "0"
another_child_pointer = pointer / "score/1"

print(child_pointer)  # "/users/score/0"
print(another_child_pointer)  # "/users/score/1"
```
