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
