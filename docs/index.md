# Python JSONPath

JSONPath is a mini language for selecting values from data formatted in JavaScript Object Notation, or equivalent Python objects, like dictionaries and lists.

Python JSONPath is a non-evaluating, read-only implementation of JSONPath, suitable for situations where JSONPath query authors are untrusted. We follow [RFC 9535](https://datatracker.ietf.org/doc/html/rfc9535) and test against the [JSONPath Compliance Test Suite](https://github.com/jsonpath-standard/jsonpath-compliance-test-suite).

We also include implementations of [JSON Pointer](pointers.md) ([RFC 6901](https://datatracker.ietf.org/doc/html/rfc6901)) and [JSON Patch](api.md#jsonpath.JSONPatch) ([RFC 6902](https://datatracker.ietf.org/doc/html/rfc6902)), plus methods for converting a [JSONPathMatch](api.md#jsonpath.JSONPathMatch) to a `JSONPointer`.

## Install

Install Python JSONPath using [pip](https://pip.pypa.io/en/stable/getting-started/):

```console
pip install python-jsonpath
```

Or [Pipenv](https://pipenv.pypa.io/en/latest/):

```console
pipenv install python-jsonpath
```

Or [pipx](https://pypa.github.io/pipx/)

```console
pipx install python-jsonpath
```

Or from [conda-forge](https://anaconda.org/conda-forge/python-jsonpath):

```console
conda install -c conda-forge python-jsonpath
```

### Optional dependencies

Python JSONPath works out of the box with **no extra dependencies**, and its syntax is already **very close** to [RFC 9535](https://www.rfc-editor.org/rfc/rfc9535).

For strict compliance with the specification, [strict mode](syntax.md) and the `strict` extra were added in **version 2.0.0**.

```console
pip install python-jsonpath[strict]
```

This installs [`regex`](https://pypi.org/project/regex/) and [`iregexp-check`](https://pypi.org/project/iregexp-check/), enabling:

- [`match()`](functions.md#match) and [`search()`](functions.md#search) to use `regex` instead of Python's built-in `re` module.
- Validation of regular expressions against [RFC 9485](https://datatracker.ietf.org/doc/html/rfc9485).

See the [syntax guide](syntax.md) for strict mode details and specification extensions.

## Example

```python
import jsonpath

example_data = {
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

products = jsonpath.findall("$..products.*", example_data)
print(products)
```

Which results in a list of all products from all categories:

```json
[
  {
    "title": "Trainers",
    "description": "Fashionable trainers.",
    "price": 89.99
  },
  {
    "title": "Barefoot Trainers",
    "description": "Running trainers.",
    "price": 130.0
  },
  {
    "title": "Cap",
    "description": "Baseball cap",
    "price": 15.0
  },
  {
    "title": "Beanie",
    "description": "Winter running hat.",
    "price": 9.0
  }
]
```

Or, reading data from a JSON formatted file:

```python
import jsonpath

with open("some.json") as fd:
    products = jsonpath.findall("$..products.*", fd)

print(products)
```

You could use Python JSONPath on data read from a YAML formatted file too, or any data format that can be loaded into dictionaries and lists. If you have [PyYAML](https://pyyaml.org/wiki/PyYAML) installed:

```python
import jsonpath
import yaml

with open("some.yaml") as fd:
    data = yaml.safe_load(fd)

products = jsonpath.findall("$..products.*", data)
print(products)
```

## Next Steps

Have a read through the [Quick Start](quickstart.md) and [High Level API Reference](api.md), or the default [JSONPath Syntax](syntax.md) supported by Python JSONPath.

If you're interested in customizing JSONPath, take a look at [Advanced Usage](advanced.md) and the [Low Level API Reference](custom_api.md).
