<h1 align="center">Python JSONPath</h1>

<p align="center">
A flexible JSONPath engine for Python with JSON Pointer and JSON Patch.
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
- [Examples](#examples)
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

Or from [conda-forge](https://anaconda.org/conda-forge/python-jsonpath):

```console
conda install -c conda-forge python-jsonpath
```

## Links

- Documentation: https://jg-rp.github.io/python-jsonpath/.
- JSONPath Syntax: https://jg-rp.github.io/python-jsonpath/syntax/
- Change log: https://github.com/jg-rp/python-jsonpath/blob/main/CHANGELOG.md
- PyPi: https://pypi.org/project/python-jsonpath
- Source code: https://github.com/jg-rp/python-jsonpath
- Issue tracker: https://github.com/jg-rp/python-jsonpath/issues

## Examples

### JSONPath

```python
import jsonpath

data = {
    "users": [
        {"name": "Sue", "score": 100},
        {"name": "John", "score": 86},
        {"name": "Sally", "score": 84},
        {"name": "Jane", "score": 55},
    ]
}

user_names = jsonpath.findall("$.users[?@.score < 100].name", data)
print(user_names) # ['John', 'Sally', 'Jane']
```

### JSON Pointer

Since version 0.8.0, we include an [RFC 6901](https://datatracker.ietf.org/doc/html/rfc6901) compliant implementation of JSON Pointer. See JSON Pointer [quick start](https://jg-rp.github.io/python-jsonpath/quickstart/#pointerresolvepointer-data), [guide](https://jg-rp.github.io/python-jsonpath/pointers/) and [API reference](https://jg-rp.github.io/python-jsonpath/api/#jsonpath.JSONPointer)

```python
from jsonpath import pointer

data = {
    "users": [
        {"name": "Sue", "score": 100},
        {"name": "John", "score": 86},
        {"name": "Sally", "score": 84},
        {"name": "Jane", "score": 55},
    ]
}

sue_score = pointer.resolve("/users/0/score", data)
print(sue_score)  # 100

jane_score = pointer.resolve(["users", 3, "score"], data)
print(jane_score)  # 55
```

### JSON Patch

Since version 0.8.0, we also include an [RFC 6902](https://datatracker.ietf.org/doc/html/rfc6902) compliant implementation of JSON Patch. See JSON Patch [quick start](https://jg-rp.github.io/python-jsonpath/quickstart/#patchapplypatch-data) and [API reference](https://jg-rp.github.io/python-jsonpath/api/#jsonpath.JSONPatch)

```python
from jsonpath import patch

patch_operations = [
    {"op": "add", "path": "/some/foo", "value": {"foo": {}}},
    {"op": "add", "path": "/some/foo", "value": {"bar": []}},
    {"op": "copy", "from": "/some/other", "path": "/some/foo/else"},
    {"op": "add", "path": "/some/foo/bar/-", "value": 1},
]

data = {"some": {"other": "thing"}}
patch.apply(patch_operations, data)
print(data) # {'some': {'other': 'thing', 'foo': {'bar': [1], 'else': 'thing'}}}

```

## License

`python-jsonpath` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
