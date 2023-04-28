<h1 align="center">Python JSONPath</h1>

<p align="center">
A flexible JSONPath engine for Python.
</p>

<p align="center">
  <a href="https://github.com/jg-rp/python-jsonpath/blob/main/LICENSE.txt">
    <img src="https://img.shields.io/pypi/l/python-jsonpath?style=flat-square" alt="License">
  </a>
  <a href="https://github.com/jg-rp/python-jsonpath/actions">
    <img src="https://img.shields.io/github/actions/workflow/status/jg-rp/python-jsonpath/tests.yaml?branch=main&label=tests&style=flat-square" alt="Tests">
  </a>
  <br>
  <a href="https://pypi.org/project/python-jsonpath">
    <img src="https://img.shields.io/pypi/v/python-jsonpath.svg?style=flat-square" alt="PyPi - Version">
  </a>
  <a href="https://pypi.org/project/python-jsonpath">
    <img src="https://img.shields.io/pypi/pyversions/python-jsonpath.svg?style=flat-square" alt="Python versions">
  </a>
</p>

---

**Table of Contents**

- [Install](#install)
- [Links](#links)
- [Example](#example)
- [License](#license)

## Install

Install Python JSONPath using [pip](https://pip.pypa.io/en/stable/getting-started/):

```console
pip install python-jsonpath
```

Or [Pipenv](https://pipenv.pypa.io/en/latest/):

```console
pipenv install -u python-jsonpath
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

user_names = jsonpath.findall("$.users[?@.score < 100].name", data)
print(user_names) # ['John', 'Sally', 'Jane']
```

## License

`python-jsonpath` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
