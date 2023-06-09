# Advanced Usage

## Filter Variables

Arbitrary variables can be made available to [filter expressions](syntax.md#filters-expression) using the _filter_context_ argument to [`findall()`](quickstart.md#findallpath-data) and [`finditer()`](quickstart.md#finditerpath-data). _filter_context_ should be a [mapping](https://docs.python.org/3/library/typing.html#typing.Mapping) of strings to JSON-like objects, like lists, dictionaries, strings and integers.

Filter context variables are selected using the _filter context selector_, which defaults to `_` and has usage similar to `$` and `@`.

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

user_names = jsonpath.findall(
    "$.users[?@.score < _.limit].name",
    data,
    filter_context={"limit": 100},
)
```

## Function Extensions

Add, remove or replace [filter functions](functions.md) by updating the [`function_extensions`](api.md#jsonpath.env.JSONPathEnvironment.function_extensions) attribute of a [`JSONPathEnvironment`](api.md#jsonpath.env.JSONPathEnvironment). It is a regular Python dictionary mapping filter function names to any [callable](https://docs.python.org/3/library/typing.html#typing.Callable), like a function or class with a `__call__` method.

### Example

As an example, we'll add a `min()` filter function, which will return the minimum of a sequence of values. If any of the values are not comparable, we'll return the special `undefined` value instead.

```python
from typing import Iterable
import jsonpath


def min_filter(obj: object) -> object:
    if not isinstance(obj, Iterable):
        return jsonpath.UNDEFINED

    try:
        return min(obj)
    except TypeError:
        return jsonpath.UNDEFINED


env = jsonpath.JSONPathEnvironment()
env.function_extensions["min"] = min_filter
```

Now, when we use `env.finall()`, `env.finditer()` or `env.compile()`, our `min` function will be available for use in filter expressions.

```text
$..products[?@.price == min($..products.price)]
```

### Built-in Functions

The [built-in functions](functions.md) can be removed from a `JSONPathEnvironment` by deleting the entry from `function_extensions`.

```python
import jsonpath

env = jsonpath.JSONPathEnvironment()
del env.function_extensions["keys"]
```

Or aliased with an additional entry.

```python
import jsonpath

env = jsonpath.JSONPathEnvironment()
env.function_extensions["properties"] = env.function_extensions["keys"]
```

Alternatively, you could subclass `JSONPathEnvironment` and override the `setup_function_extensions` method.

```python
from typing import Iterable
import jsonpath

class MyEnv(jsonpath.JSONPathEnvironment):
    def setup_function_extensions(self) -> None:
        super().setup_function_extensions()
        self.function_extensions["properties"] = self.function_extensions["keys"]
        self.function_extensions["min"] = min_filter


def min_filter(obj: object) -> object:
    if not isinstance(obj, Iterable):
        return jsonpath.UNDEFINED

    try:
        return min(obj)
    except TypeError:
        return jsonpath.UNDEFINED

env = MyEnv()
```

### Compile Time Validation

A function extension's arguments can be validated at compile time by implementing the function as a class with a `__call__` method, and a `validate` method. `validate` will be called after parsing the function, giving you the opportunity to inspect its arguments and raise a `JSONPathTypeError` should any arguments be unacceptable. If defined, `validate` must take a reference to the current environment, an argument list and the token pointing to the start of the function call.

```python
def validate(
        self,
        env: JSONPathEnvironment,
        args: List[FilterExpression],
        token: Token,
) -> List[FilterExpression]:
```

It should return an argument list, either the same as the input argument list, or a modified version of it. See the implementation of the built-in [`match` function](https://github.com/jg-rp/python-jsonpath/blob/main/jsonpath/function_extensions/match.py) for an example.

## Custom Environments

Python JSONPath can be customized by subclassing [`JSONPathEnvironment`](api.md#jsonpath.JSONPathEnvironment) and overriding class attributes and/or methods. Then using `findall()`, `finditer()` and `compile()` methods of that subclass.

### Identifier Tokens

The default identifier tokens, like `$` and `@`, can be changed by setting attributes a on `JSONPathEnvironment`. This example sets the root token (default `$`) to be `^`.

```python
import jsonpath

class MyJSONPathEnvironment(jsonpath.JSONPathEnvironment):
    root_token = "^"


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
    ],
    "limit": 100,
}

env = MyJSONPathEnvironment()
user_names = env.findall(
    "^.users[?@.score < ^.limit].name",
    data,
)
```

This table shows all available identifier token attributes.

| attribute            | default |
| -------------------- | ------- |
| filter_context_token | `_`     |
| keys_token           | `#`     |
| root_token           | `$`     |
| self_token           | `@`     |

### Operator Tokens

TODO:

### Keys Selector

TODO:

### Array Index Limits

TODO:

### Subclassing Lexer

TODO:

### Subclassing Parser

TODO:

### Get Item

TODO:

### Truthiness and Existence

TODO:

### Filter Infix Expressions

TODO:
