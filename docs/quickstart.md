# Quick Start

This page gets you starting with Python JSONPath, see [JSONPath Syntax](syntax.md) for information on JSONPath selector syntax.

## `findall`

Find all objects matching a JSONPath with [`jsonpath.findall()`](api.md#jsonpath.env.JSONPathEnvironment.findall). It takes, as arguments, a JSONPath string and some _data_ object. It always returns a list of objects selected from the given data.

_data_ can be a file-like object or string containing JSON formatted data, or a Python [`Mapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping) or [`Sequence`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Sequence), like a dictionary or list. In this example we select user names from a dictionary containing a list of user dictionaries.

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

## `finditer`

Use [`jsonpath.finditer()`](api.md#jsonpath.env.JSONPathEnvironment.finditer) to create an iterator which yields instances of [`jsonpath.JSONPathMatch`](api.md#jsonpath.JSONPathMatch) for every object in some data that matches a JSONPath. It accepts the same arguments as [`findall()`](#findall), a path string and _data_ from which to select matches.

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

## `compile`

When you have a JSONPath that needs to be matched against different data repeatedly, you can _compile_ the path ahead of time using [`jsonpath.compile()`](api.md#jsonpath.env.JSONPathEnvironment.compile). It takes a path as a string and returns a [`JSONPath`](api.md#jsonpath.JSONPath) instance. `JSONPath` has `findall()` and `finditer()` methods that behave similarly to package-level `findall()` and `finditer()`, just without the `path` argument.

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

## What's Next

Read about user-defined filter functions at [Function Extensions](advanced.md), or see how to make extra data available to filters with [Extra Filter Context](advanced.md).

`findall`, `finditer` and `compile` are shortcuts that use the default[`JSONPathEnvironment`](api.md#jsonpath.JSONPathEnvironment). `jsonpath.findall(path, data)` is equivalent to `jsonpath.JSONPathEnvironment().compile(path).findall(data)`. If you would like to use a custom environment, see [Advanced Usage](advanced.md).
