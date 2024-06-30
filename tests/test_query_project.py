"""Test cases for the fluent API projection."""

from typing import Any
from typing import List

import jsonpath


def test_top_level_array() -> None:
    expr = "$.*"
    data = [{"a": 1, "b": 1}, {"a": 2, "b": 2}, {"b": 3, "a": 3}]
    projection = ("a",)
    it = jsonpath.query(expr, data).select(*projection)
    assert list(it) == [{"a": 1}, {"a": 2}, {"a": 3}]


def test_top_level_array_partial_existence() -> None:
    expr = "$.*"
    data = [{"a": 1, "b": 1}, {"b": 2}, {"b": 3, "a": 3}]
    projection = ("a",)
    it = jsonpath.query(expr, data).select(*projection)
    assert list(it) == [{"a": 1}, {"a": 3}]


def test_top_level_array_projection_does_not_existence() -> None:
    expr = "$.*"
    data = [{"a": 1, "b": 1}, {"b": 2}, {"b": 3, "a": 3}]
    projection = ("x",)
    it = jsonpath.query(expr, data).select(*projection)
    assert list(it) == []


def test_empty_top_level_array() -> None:
    expr = "$.*"
    data: List[Any] = []
    projection = ("a",)
    it = jsonpath.query(expr, data).select(*projection)
    assert list(it) == []


def test_top_level_array_select_many() -> None:
    expr = "$.*"
    data = [{"a": 1, "b": 1, "c": 1}, {"a": 2, "b": 2, "c": 2}, {"b": 3, "a": 3}]
    projection = ("a", "c")
    it = jsonpath.query(expr, data).select(*projection)
    assert list(it) == [{"a": 1, "c": 1}, {"a": 2, "c": 2}, {"a": 3}]


def test_singular_query() -> None:
    expr = "$.a"
    data = {"a": {"foo": 42, "bar": 7}, "b": 1}
    projection = ("foo",)
    it = jsonpath.query(expr, data).select(*projection)
    assert list(it) == [{"foo": 42}]


def test_select_array_element() -> None:
    expr = "$.a"
    data = {"a": {"foo": [42, 7], "bar": 7}, "b": 1}
    projection = ("foo[0]",)
    it = jsonpath.query(expr, data).select(*projection)
    assert list(it) == [{"foo": [42]}]


def test_select_array_slice() -> None:
    expr = "$.a"
    data = {"a": {"foo": [1, 2, 42, 7, 3], "bar": 7}, "b": 1}
    projection = ("foo[2:4]",)
    it = jsonpath.query(expr, data).select(*projection)
    assert list(it) == [{"foo": [42, 7]}]


def test_select_nested_objects() -> None:
    expr = "$.a"
    data = {"a": {"foo": {"bar": 42}, "bar": 7}, "b": 1}
    projection = ("foo.bar",)
    it = jsonpath.query(expr, data).select(*projection)
    assert list(it) == [{"foo": {"bar": 42}}]
