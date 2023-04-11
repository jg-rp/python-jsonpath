# Python JSONPath

[![PyPI - Version](https://img.shields.io/pypi/v/python-jsonpath.svg?style=flat-square)](https://pypi.org/project/python-jsonpath)
[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/jg-rp/python-jsonpath/tests.yaml?branch=main&label=tests&style=flat-square)](https://github.com/jg-rp/python-jsonpath/actions)
[![PyPI - License](https://img.shields.io/pypi/l/python-jsonpath?style=flat-square)](https://github.com/jg-rp/python-jsonpath/blob/main/LICENSE.txt)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/python-jsonpath.svg?style=flat-square)](https://pypi.org/project/python-jsonpath)

---

A flexible JSONPath engine for Python.

**Table of Contents**

- [Install](#install)
- [Links](#links)
- [Example](#example)
- [License](#license)

## Install

Install Python JSONPath using [Pipenv](https://pipenv.pypa.io/en/latest/):

```console
pipenv install -u python-jsonpath
```

or [pip](https://pip.pypa.io/en/stable/getting-started/):

```console
pip install python-jsonpath
```

## Links

- Documentation: https://jg-rp.github.io/python-jsonpath/.
- JSONPath Syntax: https://jg-rp.github.io/python-jsonpath/syntax/
- Change log: https://github.com/jg-rp/python-jsonpath/blob/main/CHANGELOG.md
- PyPi: https://pypi.org/project/python-jsonpath
- Source code: https://github.com/jg-rp/python-jsonpath
- Issue tracker: https://github.com/jg-rp/python-jsonpath/issues

## Example

```python
import jsonpath

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

products = jsonpath.findall("$..products.*", data)
print(products)
```

## License

`python-jsonpath` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
