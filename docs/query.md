# Query Iterators

**_New in version 1.1.0_**

In addition to [`findall()`](api.md#jsonpath.JSONPathEnvironment.findall) and [`finditer()`](api.md#jsonpath.JSONPathEnvironment.finditer), covered in the [quick start guide](./quickstart.md), Python JSONPath offers a fluent _query iterator_ interface.

[`Query`](api.md#jsonpath.Query) objects provide chainable methods for manipulating a [`JSONPathMatch`](api.md#jsonpath.JSONPathMatch) iterator, like you'd get from `finditer()`. Obtain a `Query` object using the package-level `query()` function, [`JSONPathEnvironment.query()`](api.md#jsonpath.JSONPathEnvironment.query) or using the [`query()`](api.md#jsonpath.JSONPath.query) method of a compiled JSONPath.

This example uses the query API to skip the first five matches, limit the total number of matches to ten, then get the value associated with each match.

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

| Method          | Aliases         | Description                                        |
| --------------- | --------------- | -------------------------------------------------- |
| `skip(n: int)`  | `drop`          | Drop up to _n_ matches from the iterator.          |
| `limit(n: int)` | `head`, `first` | Yield at most _n_ matches from the iterator.       |
| `tail(n: int)`  | `last`          | Drop matches from the iterator up to the last _n_. |

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

## Take

[`Query.take(self, n: int)`](api.md#jsonpath.Query.take) returns a new `Query` instance, iterating over the next _n_ matches. It leaves the existing query in a safe state, ready to resume iteration of remaining matches.

```python
from jsonpath import query

it = query("$.some.*", {"some": [0, 1, 2, 3]})

for match in it.take(2):
    print(match.value)  # 0, 1

for value in it.values():
    print(value)  # 2, 3
```

## Tee

[`tee()`](api.md#jsonpath.Query.tee) creates multiple independent queries from one query iterator. It is not safe to use the initial `Query` instance after calling `tee()`.

```python
from jsonpath import query

it1, it2 = query("$.some[?@.thing]", data).tee()

head = it1.head(10) # first 10 matches
tail = it2.tail(10) # last 10 matches
```

## Select

[`select(*expressions, projection=Projection.RELATIVE)`](api.md/#jsonpath.Query.select) performs JSONPath match projection, selecting a subset of values according to one or more JSONPath query expressions relative to the match location. For example:

```python
from jsonpath import query

data = {
    "categories": [
        {
            "name": "footwear",
            "products": [
                {
                    "title": "Trainers",
                    "description": "Fashionable trainers.",
                    "price": 89.99,
                },
                {
                    "title": "Barefoot Trainers",
                    "description": "Running trainers.",
                    "price": 130.00,
                    "social": {"likes": 12, "shares": 7},
                },
            ],
        },
        {
            "name": "headwear",
            "products": [
                {
                    "title": "Cap",
                    "description": "Baseball cap",
                    "price": 15.00,
                },
                {
                    "title": "Beanie",
                    "description": "Winter running hat.",
                    "price": 9.00,
                },
            ],
        },
    ],
    "price_cap": 10,
}

for product in query("$..products.*", data).select("title", "price"):
    print(product)
```

Which selects just the `title` and `price` fields for each product.

```text
{'title': 'Trainers', 'price': 89.99}
{'title': 'Barefoot Trainers', 'price': 130.0}
{'title': 'Cap', 'price': 15.0}
{'title': 'Beanie', 'price': 9.0}
```

Without the call to `select()`, we'd get all fields in each product object.

```python
# ...

for product in query("$..products.*", data).values():
    print(product)
```

```text
{'title': 'Trainers', 'description': 'Fashionable trainers.', 'price': 89.99}
{'title': 'Barefoot Trainers', 'description': 'Running trainers.', 'price': 130.0, 'social': {'likes': 12, 'shares': 7}}
{'title': 'Cap', 'description': 'Baseball cap', 'price': 15.0}
{'title': 'Beanie', 'description': 'Winter running hat.', 'price': 9.0}
```

We can select nested values too.

```python
# ...

for product in query("$..products.*", data).select("title", "social.shares"):
    print(product)
```

```text
{'title': 'Trainers'}
{'title': 'Barefoot Trainers', 'social': {'shares': 7}}
{'title': 'Cap'}
{'title': 'Beanie'}
```

And flatten the selection into a sequence of values.

```python
from jsonpath import Projection

# ...

for product in query("$..products.*", data).select(
    "title", "social.shares", projection=Projection.FLAT
):
    print(product)
```

```text
['Trainers']
['Barefoot Trainers', 7]
['Cap']
['Beanie']
```

Or project the selection from the JSON value root.

```python
# ..

for product in query("$..products[?@.social]", data).select(
    "title",
    "social.shares",
    projection=Projection.ROOT,
):
    print(product)

```

```text
{'categories': [{'products': [{'title': 'Barefoot Trainers', 'social': {'shares': 7}}]}]}
```
