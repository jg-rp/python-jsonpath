# Quick Start

This page gets you started using JSONPath, JSON Pointer and JSON Patch wih Python. See [JSONPath Syntax](syntax.md) for information on JSONPath selector syntax.

## `findall(path, data)`

Find all values matching a JSONPath expression using [`jsonpath.findall()`](api.md#jsonpath.JSONPathEnvironment.findall).

This function takes two arguments:

- `path`: a JSONPath expression as a string (e.g., `"$.users[*].name"`)
- `data`: the JSON document to query

It always returns a **list** of matched values, even if the path resolves to a single result or nothing at all.

The `data` argument can be:

- A Python [`Mapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping) (e.g., `dict`) or [`Sequence`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Sequence) (e.g., `list`)
- A JSON-formatted string
- A file-like object containing JSON

For example, the following query extracts all user names from a dictionary containing a list of user objects:

```python
import jsonpath

data = {
    "users": [
        {
            "name": "Sue",
            "score": 100,
        },
        {
            "name": "John",
            "score": 86,
        },
        {
            "name": "Sally",
            "score": 84,
        },
        {
            "name": "Jane",
            "score": 55,
        },
    ]
}

user_names = jsonpath.findall("$.users.*.name", data)
```

Where `user_names` is now equal to:

```json
["Sue", "John", "Sally", "Jane"]
```

If the same data were in a file called `users.json`, we might use `findall()` like this:

```python
import jsonpath

with open("users.json") as fd:
    user_names = jsonpath.findall("$.users.*.name", fd)
```

## `finditer(path, data)`

Use [`jsonpath.finditer()`](api.md#jsonpath.JSONPathEnvironment.finditer) to iterate over instances of [`jsonpath.JSONPathMatch`](api.md#jsonpath.JSONPathMatch) for every object in _data_ that matches _path_. It accepts the same arguments as [`findall()`](#findallpath-data), a path string and data from which to select matches.

```python
import jsonpath

data = {
    "users": [
        {
            "name": "Sue",
            "score": 100,
        },
        {
            "name": "John",
            "score": 86,
        },
        {
            "name": "Sally",
            "score": 84,
        },
        {
            "name": "Jane",
            "score": 55,
        },
    ]
}

matches = jsonpath.finditer("$.users.*.name", data)
for match in matches:
    print(matches)
```

The string representation of a [`JSONPathMatch`](api.md#jsonpath.JSONPathMatch) shows the matched object and the canonical path to that object.

```text
'Sue' @ $['users'][0]['name']
'John' @ $['users'][1]['name']
'Sally' @ $['users'][2]['name']
'Jane' @ $['users'][3]['name']
```

The selected object is available from a [`JSONPathMatch`](api.md#jsonpath.JSONPathMatch) as `obj` and its path, as a string, as `path`. Other useful properties of `JSONPathMatch` include a reference to the parent match, a list of child matches, and a `parts` tuple of keys and indices that make up the path.

## `compile(path)`

When you have a JSONPath that needs to be matched against different data repeatedly, you can _compile_ the path ahead of time using [`jsonpath.compile()`](api.md#jsonpath.JSONPathEnvironment.compile). It takes a path as a string and returns a [`JSONPath`](api.md#jsonpath.JSONPath) instance. `JSONPath` has `findall()` and `finditer()` methods that behave similarly to package-level `findall()` and `finditer()`, just without the `path` argument.

```python
import jsonpath

some_data = {
    "users": [
        {
            "name": "Sue",
            "score": 100,
        },
        {
            "name": "John",
            "score": 86,
        },
    ]
}

other_data = {
    "users": [
        {
            "name": "Sally",
            "score": 84,
        },
        {
            "name": "Jane",
            "score": 55,
        },
    ]
}

path = jsonpath.compile("$.users.*.name")

some_users = path.findall(some_data)
other_users = path.findall(other_data)
```

## `match(path, data)`

**_New in version 0.8.0_**

Get a [`jsonpath.JSONPathMatch`](api.md#jsonpath.JSONPathMatch) instance for the first match found in _data_. If there are no matches, `None` is returned. `match()` accepts the same arguments as [`findall()`](#findallpath-data).

```python
import jsonpath

data = {
    "users": [
        {
            "name": "Sue",
            "score": 100,
        },
        {
            "name": "John",
            "score": 86,
        },
        {
            "name": "Sally",
            "score": 84,
        },
        {
            "name": "Jane",
            "score": 55,
        },
    ]
}

match = jsonpath.match("$.users[?@.score > 85].name", data)
if match:
    print(match)  # 'Sue' @ $['users'][0]['name']
    print(match.obj)  # Sue
```

## `pointer.resolve(pointer, data)`

**_New in version 0.8.0_**

Resolves a JSON Pointer ([RFC 6901](https://datatracker.ietf.org/doc/html/rfc6901)) against a JSON document, returning the value located at the specified path.

The `pointer` argument can be either:

- A string representation of a JSON Pointer (e.g., `"/foo/bar/0"`)
- A list of unescaped pointer segments (e.g., `["foo", "bar", "0"]`)

The `data` argument can be:

- A Python data structure (`dict`, `list`, etc.)
- A JSON-formatted string
- A file-like object containing JSON

```python
from jsonpath import pointer

data = {
    "users": [
        {
            "name": "Sue",
            "score": 100,
        },
        {
            "name": "John",
            "score": 86,
        },
        {
            "name": "Sally",
            "score": 84,
        },
        {
            "name": "Jane",
            "score": 55,
        },
    ]
}

sue_score = pointer.resolve("/users/0/score", data)
print(sue_score)  # 100

jane_score = pointer.resolve(["users", 3, "score"], data)
print(jane_score)  # 55
```

If the pointer cannot be resolved against the target JSON data — due to a missing key, an out-of-range index, or an unexpected data type — an exception will be raised:

- `JSONPointerKeyError` – when a referenced key is missing from an object
- `JSONPointerIndexError` – when an array index is out of bounds
- `JSONPointerTypeError` – when a path segment expects the wrong type (e.g., indexing into a non-array)

All of these exceptions are subclasses of `JSONPointerResolutionError`.

You can optionally provide a `default` value to `resolve()`, which will be returned instead of raising an error if the pointer cannot be resolved.

```python
from jsonpath import pointer

data = {
    "users": [
        {
            "name": "Sue",
            "score": 100,
        },
        {
            "name": "John",
            "score": 86,
        },
    ]
}

sue_score = pointer.resolve("/users/99/score", data, default=0)
print(sue_score)  # 0
```

See also [`JSONPathMatch.pointer()`](api.md#jsonpath.JSONPathMatch.pointer), which builds a [`JSONPointer`](api.md#jsonpath.JSONPointer) from a `JSONPathMatch`.

## `patch.apply(patch, data)`

**_New in version 0.8.0_**

Apply a JSON Patch ([RFC 6902](https://datatracker.ietf.org/doc/html/rfc6902)) to some data. A JSON Patch defines update operation to perform on a JSON document.

_patch_ can be a string or file-like object containing a valid JSON Patch document, or an iterable of dictionaries.

_data_ is the target JSON document to modify. If _data_ is a string or file-like object, it will be loaded with _json.loads_. Otherwise _data_ should be a JSON-like data structure and will be **modified in place**.

```python
from jsonpath import patch

patch_operations = [
    {"op": "add", "path": "/some/foo", "value": {"foo": {}}},
    {"op": "add", "path": "/some/foo", "value": {"bar": []}},
    {"op": "copy", "from": "/some/other", "path": "/some/foo/else"},
    {"op": "add", "path": "/some/foo/bar/-", "value": 1},
]

data = {"some": {"other": "thing"}}
patch.apply(patch_operations, data)
print(data) # {'some': {'other': 'thing', 'foo': {'bar': [1], 'else': 'thing'}}}
```

Use the [JSONPatch](api.md#jsonpath.JSONPatch) class to create a patch for repeated application.

```python
from jsonpath import JSONPatch

patch = JSONPatch(
    [
        {"op": "add", "path": "/some/foo", "value": {"foo": {}}},
        {"op": "add", "path": "/some/foo", "value": {"bar": []}},
        {"op": "copy", "from": "/some/other", "path": "/some/foo/else"},
        {"op": "add", "path": "/some/foo/bar/-", "value": 1},
    ]
)

data = {"some": {"other": "thing"}}
patch.apply(data)
print(data)  # {'some': {'other': 'thing', 'foo': {'bar': [1], 'else': 'thing'}}}
```

[JSONPatch](api.md#jsonpath.JSONPatch) also offers a builder API for constructing JSON patch documents. We use strings as JSON Pointers in this example, but existing [JSONPointer](api.md#jsonpath.JSONPointer) instances are OK too.

```python
from jsonpath import JSONPatch

patch = (
    JSONPatch()
    .add("/some/foo", {"foo": []})
    .add("/some/foo", {"bar": []})
    .copy("/some/other", "/some/foo/else")
    .add("/some/foo/bar/-", "/some/foo/else")
)

data = {"some": {"other": "thing"}}
patch.apply(data)
print(data)  # {'some': {'other': 'thing', 'foo': {'bar': [1], 'else': 'thing'}}}
```

## What's Next?

Read about the [Query Iterators](query.md) API or [user-defined filter functions](advanced.md#function-extensions). Also see how to make extra data available to filters with [Extra Filter Context](advanced.md#filter-variables).

`findall()`, `finditer()` and `compile()` are shortcuts that use the default[`JSONPathEnvironment`](api.md#jsonpath.JSONPathEnvironment). `jsonpath.findall(path, data)` is equivalent to:

```python
jsonpath.JSONPathEnvironment().compile(path).findall(data)
```

If you would like to customize Python JSONPath, see [Advanced Usage](advanced.md#custom-environments).
