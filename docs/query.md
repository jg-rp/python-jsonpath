# Query Iterators

**_New in version 1.1.0_**

In addition to [`findall()`](api.md#jsonpath.JSONPathEnvironment.findall) and [`finditer()`](api.md#jsonpath.JSONPathEnvironment.finditer), covered in the [quick start guide](./quickstart.md), Python JSONPath offers a fluent _query_ iterator interface.

[`Query`](api.md#jsonpath.Query) objects provide chainable methods for manipulating a [`JSONPathMatch`](api.md#jsonpath.JSONPathMatch) iterator, just like you'd get from `finditer()`. Obtain a `Query` object using the package-level `query()` function or [`JSONPathEnvironment.query()`](api.md#jsonpath.JSONPathEnvironment.query).

This example uses the query API to skip the first 5 matches, limit the total number of matches to 10, and get the value associated with each match.

```python
from jsonpath import query

# data = ...

values = (
    query("$.some[?@.thing]", data)
    .skip(5)
    .limit(10)
    .values()
)

for value in values:
    # ...
```

`Query` objects are iterable and can only be iterated once. Pass the query to `list()` (or other sequence) to get a list of results that can be iterated multiple times or otherwise manipulated.

```python
from jsonpath import query

# data = ...

values = list(
    query("$.some[?@.thing]", data)
    .skip(5)
    .limit(10)
    .values()
)

print(values[1])
```

## Chainable methods

The following `Query` methods all return `self` (the same `Query` instance), so method calls can be chained to further manipulate the underlying iterator.

| Method          | Aliases                 | Description                                        |
| --------------- | ----------------------- | -------------------------------------------------- |
| `skip(n: int)`  | `drop`                  | Drop up to _n_ matches from the iterator.          |
| `limit(n: int)` | `head`, `take`, `first` | Yield at most _n_ matches from the iterator.       |
| `tail(n: int)`  | `last`                  | Drop matches from the iterator up to the last _n_. |

## Terminal methods

These are terminal methods of the `Query` class. They can not be chained.

| Method        | Aliases | Description                                                                                 |
| ------------- | ------- | ------------------------------------------------------------------------------------------- |
| `values()`    |         | Return an iterable of objects, one for each match in the iterable.                          |
| `locations()` |         | Return an iterable of normalized paths, one for each match in the iterable.                 |
| `items()`     |         | Return an iterable of (object, normalized path) tuples, one for each match in the iterable. |
| `pointers()`  |         | Return an iterable of `JSONPointer` instances, one for each match in the iterable.          |
| `first_one()` | `one`   | Return the first `JSONPathMatch`, or `None` if there were no matches.                       |
| `last_one()`  |         | Return the last `JSONPathMatch`, or `None` if there were no matches.                        |

## Tee

And finally there's `tee()`, which creates multiple independent queries from one query iterator. It is not safe to use the initial `Query` instance after calling `tee()`.

```python
from jsonpath import query

it1, it2 = query("$.some[?@.thing]", data).tee()

head = it1.head(10) # first 10 matches
tail = it2.tail(10) # last 10 matches
```
