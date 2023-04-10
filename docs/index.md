# Python JSONPath

JSONPath is a mini language for selecting objects from data formatted in JavaScript Object Notation, or equivalent Python objects, like dictionaries and lists.

## Install

Install Python JSONPath using [pip](https://pip.pypa.io/en/stable/getting-started/):

```console
pip install python-jsonpath
```

Or [Pipenv](https://pipenv.pypa.io/en/latest/):

```console
pipenv install python-jsonpath
```

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
