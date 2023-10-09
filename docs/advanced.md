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

### Type System for Function Expressions

[Section 2.4.1](https://datatracker.ietf.org/doc/html/draft-ietf-jsonpath-base-21#section-2.4.1) of the IETF JSONPath Draft specification defines a type system for function expressions and requires that we check that filter expressions are well-typed. With that in mind, you are encouraged to implement custom filter functions by extending [`jsonpath.function_extensions.FilterFunction`](api.md#jsonpath.function_extensions.FilterFunction), which forces you to be explicit about the [types](api.md#jsonpath.function_extensions.ExpressionType) of arguments the function extension accepts and the type of its return value.

!!! info

    [`FilterFunction`](api.md#jsonpath.function_extensions.FilterFunction) was new in Python JSONPath version 0.10.0. Prior to that we did not enforce function expression well-typedness. To use any arbitrary [callable](https://docs.python.org/3/library/typing.html#typing.Callable) as a function extension - or if you don't want built-in filter functions to raise a `JSONPathTypeError` for function expressions that are not well-typed - set [`well_typed`](api.md#jsonpath.env.JSONPathEnvironment.well_typed) to `False` when constructing a [`JSONPathEnvironment`](api.md#jsonpath.env.JSONPathEnvironment).

### Example

As an example, we'll add a `min()` filter function, which will return the minimum of a sequence of values. If any of the values are not comparable, we'll return the special `undefined` value instead.

```python
from typing import Iterable

import jsonpath
from jsonpath.function_extensions import ExpressionType
from jsonpath.function_extensions import FilterFunction


class MinFilterFunction(FilterFunction):
    """A JSONPath function extension returning the minimum of a sequence."""

    arg_types = [ExpressionType.VALUE]
    return_type = ExpressionType.VALUE

    def __call__(self, value: object) -> object:
        if not isinstance(value, Iterable):
            return jsonpath.UNDEFINED

        try:
            return min(value)
        except TypeError:
            return jsonpath.UNDEFINED


env = jsonpath.JSONPathEnvironment()
env.function_extensions["min"] = MinFilterFunction()

example_data = {"foo": [{"bar": [4, 5]}, {"bar": [1, 5]}]}
print(env.findall("$.foo[?min(@.bar) > 1]", example_data))
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

Calls to [type-aware](#type-system-for-function-expressions) function extension are validated at JSONPath compile-time automatically. If [`well_typed`](api.md#jsonpath.env.JSONPathEnvironment.well_typed) is set to `False` or a custom function extension does not inherit from [`FilterFunction`](api.md#jsonpath.function_extensions.FilterFunction), its arguments can be validated by implementing the function as a class with a `__call__` method, and a `validate` method. `validate` will be called after parsing the function, giving you the opportunity to inspect its arguments and raise a `JSONPathTypeError` should any arguments be unacceptable. If defined, `validate` must take a reference to the current environment, an argument list and the token pointing to the start of the function call.

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
import JSONPathEnvironment

class MyJSONPathEnvironment(JSONPathEnvironment):
    root_token = "^"


data = {
    "users": [
        {"name": "Sue", "score": 100},
        {"name": "John", "score": 86},
        {"name": "Sally", "score": 84},
        {"name": "Jane", "score": 55},
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

### Logical Operator Tokens

TODO:

### Keys Selector

The non-standard keys selector is used to retrieve the keys/properties from a JSON Object or Python mapping. It defaults to `~` and can be changed using the `keys_selector_token` attribute on a [`JSONPathEnvironment`](./api.md#jsonpath.JSONPathEnvironment) subclass.

This example changes the keys selector to `*~`.

```python
from jsonpath import JSONPathEnvironment

class MyJSONPathEnvironment(JSONPathEnvironment):
    keys_selector_token = "*~"

data = {
    "users": [
        {"name": "Sue", "score": 100},
        {"name": "John", "score": 86},
        {"name": "Sally", "score": 84},
        {"name": "Jane", "score": 55},
    ],
    "limit": 100,
}

env = MyJSONPathEnvironment()
print(env.findall("$.users[0].*~", data))  # ['name', 'score']
```

### Array Index Limits

Python JSONPath limits the minimum and maximum JSON array or Python sequence indices (including slice steps) allowed in a JSONPath query. The default minimum allowed index is set to `-(2**53) + 1`, and the maximum to `(2**53) - 1`. When a limit is reached, a `JSONPathIndexError` is raised.

You can change the minimum and maximum allowed indices using the `min_int_index` and `max_int_index` attributes on a [`JSONPathEnvironment`](./api.md#jsonpath.JSONPathEnvironment) subclass.

```python
from jsonpath import JSONPathEnvironment

class MyJSONPathEnvironment(JSONPathEnvironment):
    min_int_index = -100
    max_int_index = 100

env = MyJSONPathEnvironment()
query = env.compile("$.users[999]")
# jsonpath.exceptions.JSONPathIndexError: index out of range, line 1, column 8
```

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
