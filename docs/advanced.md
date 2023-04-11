# Advanced Usage

## Function Extensions

Add, remove or replace [filter functions](functions.md) by updating [`JSONPathEnvironment.function_extensions`](api.md#jsonpath.env.JSONPathEnvironment.function_extensions). It is a regular Python dictionary mapping the name of the function to any [Callable](https://docs.python.org/3/library/typing.html#typing.Callable), like a function or class with a `__call__` method.

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

## Extra Filter Context

TODO:

## Custom Environments

TODO:

## Undefined

TODO:
