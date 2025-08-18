import pytest

from jsonpath import JSONPathEnvironment


@pytest.fixture()
def env() -> JSONPathEnvironment:
    return JSONPathEnvironment(strict=False)


def test_leading_whitespace(env: JSONPathEnvironment) -> None:
    query = "  $.a"
    data = {"a": 1}
    assert env.findall(query, data) == [1]


def test_trailing_whitespace(env: JSONPathEnvironment) -> None:
    query = "$.a  "
    data = {"a": 1}
    assert env.findall(query, data) == [1]


def test_index_as_object_name(env: JSONPathEnvironment) -> None:
    query = "$.a[0]"
    data = {"a": {"0": 1}}
    assert env.findall(query, data) == [1]


def test_alternative_and(env: JSONPathEnvironment) -> None:
    query = "$[?@.a and @.b]"
    data = [{"a": True, "b": False}]
    assert env.findall(query, data) == [{"a": True, "b": False}]


def test_alternative_or(env: JSONPathEnvironment) -> None:
    query = "$[?@.a or @.c]"
    data = [{"a": True, "b": False}, {"c": 99}]
    assert env.findall(query, data) == [{"a": True, "b": False}, {"c": 99}]
