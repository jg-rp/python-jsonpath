"""JSON Patch equality for Python containers."""

from collections import OrderedDict
from collections import UserDict
from collections import UserList
from collections import UserString
from types import MappingProxyType
from typing import Dict
from typing import List

import pytest

from jsonpath import JSONPatch
from jsonpath.exceptions import JSONPatchTestFailure


class ListValue(List[object]):
    pass


class OtherListValue(List[object]):
    pass


class DictValue(Dict[str, object]):
    pass


class OtherDictValue(Dict[str, object]):
    pass


@pytest.mark.parametrize(
    ("actual", "expected", "matches"),
    [
        ((True,), (1,), False),
        (([False],), ([0],), False),
        (UserList([True]), UserList([1]), False),
        (UserList([1, False]), UserList([1.0, False]), True),
        ((1, False), (1.0, False), True),
        ([1], (1,), False),
        ([1], 1, False),
        ({"a": 1}, 1, False),
        ([], (), False),
        ([1], UserList([1]), False),
        (ListValue([1, True]), [1.0, True], True),
        (ListValue([1]), OtherListValue([1]), False),
        ({"a": 1}, UserDict({"a": 1}), False),
        ({"a": 1}, MappingProxyType({"a": 1}), False),
        (UserDict({"a": True}), UserDict({"a": 1}), False),
        (UserDict({"a": 1}), UserDict({"a": 1.0}), True),
        (DictValue(a=1), {"a": 1.0}, True),
        (DictValue(a=1), OtherDictValue(a=1), False),
        (OrderedDict([("a", 1), ("b", True)]), {"b": True, "a": 1.0}, True),
        ({1: "foo"}, {1.0: "foo"}, True),
        (UserString("value"), "value", True),
        (bytearray(b"value"), b"value", True),
        ("value", b"value", False),
        ({(True, False): "a"}, {(1, 0): "a"}, False),
    ],
)
@pytest.mark.parametrize("reverse", [False, True])
def test_python_container_equality(
    actual: object, expected: object, *, matches: bool, reverse: bool
) -> None:
    if reverse:
        actual, expected = expected, actual
    data = {"value": actual}
    patch = JSONPatch().test("/value", expected)
    if matches:
        assert patch.apply(data) is data
    else:
        with pytest.raises(JSONPatchTestFailure):
            patch.apply(data)


@pytest.mark.parametrize(("boolean", "number"), [(True, 1), (False, 0), (True, 1.0)])
@pytest.mark.parametrize("value", ["foo", True, 1])
@pytest.mark.parametrize("reverse", [False, True])
def test_boolean_mapping_key_is_not_numeric(
    *, boolean: bool, number: float, value: object, reverse: bool
) -> None:
    actual = {boolean: value}
    expected = {number: value}
    left, right = (expected, actual) if reverse else (actual, expected)
    with pytest.raises(JSONPatchTestFailure):
        JSONPatch().test("/value", right).apply({"value": left})


@pytest.mark.parametrize("key", [False, True])
@pytest.mark.parametrize("value", ["foo", True, 1])
def test_matching_boolean_mapping_keys(value: object, *, key: bool) -> None:
    data = {"value": {key: value}}
    assert JSONPatch().test("/value", {key: value}).apply(data) is data


def test_deep_python_sequences() -> None:
    actual: object = True
    expected: object = 1
    for _ in range(600):
        actual = UserList([actual])
        expected = UserList([expected])
    with pytest.raises(JSONPatchTestFailure):
        JSONPatch().test("/value", expected).apply({"value": actual})


def test_recursive_python_sequences() -> None:
    actual: UserList[object] = UserList()
    expected: UserList[object] = UserList()
    actual.append(actual)
    expected.append(expected)
    data = {"value": actual}
    assert JSONPatch().test("/value", expected).apply(data) is data
    expected.append(False)
    with pytest.raises(JSONPatchTestFailure):
        JSONPatch().test("/value", expected).apply(data)


def test_identical_python_scalar() -> None:
    value = float("nan")
    data = {"value": value}
    assert JSONPatch().test("/value", value).apply(data) is data
    with pytest.raises(JSONPatchTestFailure):
        JSONPatch().test("/value", float("nan")).apply(data)
