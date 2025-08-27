import pytest

from jsonpath import JSONPathEnvironment
from jsonpath import JSONPathNameError


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


def test_alternative_null(env: JSONPathEnvironment) -> None:
    query = "$[?@.a==Null]"
    data = [{"a": None, "d": "e"}, {"a": "c", "d": "f"}]
    assert env.findall(query, data) == [{"a": None, "d": "e"}]


def test_none(env: JSONPathEnvironment) -> None:
    query = "$[?@.a==None]"
    data = [{"a": None, "d": "e"}, {"a": "c", "d": "f"}]
    assert env.findall(query, data) == [{"a": None, "d": "e"}]


def test_implicit_root_identifier(
    env: JSONPathEnvironment,
) -> None:
    query = "a['p']"
    data = {
        "a": {"j": [1, 2, 3], "p": {"q": [4, 5, 6]}},
        "b": ["j", "p", "q"],
    }

    assert env.findall(query, data) == [{"q": [4, 5, 6]}]


def test_singular_path_selector_without_root_identifier(
    env: JSONPathEnvironment,
) -> None:
    query = "$.a[b[1]]"
    data = {
        "a": {"j": [1, 2, 3], "p": {"q": [4, 5, 6]}},
        "b": ["j", "p", "q"],
        "c d": {"x": {"y": 1}},
    }

    assert env.findall(query, data) == [{"q": [4, 5, 6]}]


def test_isinstance_is_disabled_in_strict_mode() -> None:
    env = JSONPathEnvironment(strict=True)

    query = "$.some[?is(@.thing, 'string')]"
    with pytest.raises(JSONPathNameError):
        env.compile(query)

    query = "$.some[?isinstance(@.thing, 'string')]"
    with pytest.raises(JSONPathNameError):
        env.compile(query)


def test_typeof_is_disabled_in_strict_mode() -> None:
    env = JSONPathEnvironment(strict=True)

    query = "$.some[?type(@.thing) == 'string']"
    with pytest.raises(JSONPathNameError):
        env.compile(query)

    query = "$.some[?typeof(@.thing) == 'string']"
    with pytest.raises(JSONPathNameError):
        env.compile(query)


def test_startswith_is_disabled_in_strict_mode() -> None:
    env = JSONPathEnvironment(strict=True)
    query = "$[?startswith(@, 'ab')]"
    with pytest.raises(JSONPathNameError):
        env.compile(query)
