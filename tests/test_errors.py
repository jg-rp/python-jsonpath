from operator import attrgetter
from typing import Any
from typing import List
from typing import NamedTuple

import pytest

from jsonpath import JSONPathEnvironment
from jsonpath.exceptions import JSONPathRecursionError
from jsonpath.exceptions import JSONPathSyntaxError
from jsonpath.exceptions import JSONPathTypeError


@pytest.fixture()
def env() -> JSONPathEnvironment:
    return JSONPathEnvironment()


def test_unclosed_selection_list(env: JSONPathEnvironment) -> None:
    with pytest.raises(JSONPathSyntaxError, match=r"unexpected end of segment"):
        env.compile("$[1,2")


def test_function_missing_param(env: JSONPathEnvironment) -> None:
    with pytest.raises(JSONPathTypeError):
        env.compile("$[?(length()==1)]")


def test_function_too_many_params(env: JSONPathEnvironment) -> None:
    with pytest.raises(JSONPathTypeError):
        env.compile("$[?(length(@.a, @.b)==1)]")


def test_non_singular_query_is_not_comparable(env: JSONPathEnvironment) -> None:
    with pytest.raises(JSONPathTypeError):
        env.compile("$[?@.* > 2]")


def test_unbalanced_parens(env: JSONPathEnvironment) -> None:
    with pytest.raises(JSONPathSyntaxError):
        env.compile("$[?((@.foo)]")


def test_root_dot(env: JSONPathEnvironment) -> None:
    with pytest.raises(JSONPathSyntaxError):
        env.compile("$.")


def test_embedded_query_is_not_singular(env: JSONPathEnvironment) -> None:
    with pytest.raises(JSONPathSyntaxError):
        env.compile("$.a[$.*]")


class FilterLiteralTestCase(NamedTuple):
    description: str
    query: str


BAD_FILTER_LITERAL_TEST_CASES: List[FilterLiteralTestCase] = [
    FilterLiteralTestCase("just true", "$[?true]"),
    FilterLiteralTestCase("just string", "$[?'foo']"),
    FilterLiteralTestCase("just int", "$[?2]"),
    FilterLiteralTestCase("just float", "$[?2.2]"),
    FilterLiteralTestCase("just null", "$[?null]"),
    FilterLiteralTestCase("literal and literal", "$[?true && false]"),
    FilterLiteralTestCase("literal or literal", "$[?true || false]"),
    FilterLiteralTestCase("comparison and literal", "$[?true == false && false]"),
    FilterLiteralTestCase("comparison or literal", "$[?true == false || false]"),
    FilterLiteralTestCase("literal and comparison", "$[?true && true == false]"),
    FilterLiteralTestCase("literal or comparison", "$[?false || true == false]"),
]


@pytest.mark.parametrize(
    "case", BAD_FILTER_LITERAL_TEST_CASES, ids=attrgetter("description")
)
def test_filter_literals_must_be_compared(
    env: JSONPathEnvironment, case: FilterLiteralTestCase
) -> None:
    with pytest.raises(JSONPathSyntaxError):
        env.compile(case.query)


def test_recursive_data() -> None:
    class MockEnv(JSONPathEnvironment):
        nondeterministic = False

    env = MockEnv()
    query = "$..a"
    arr: List[Any] = []
    data: Any = {"foo": arr}
    arr.append(data)

    with pytest.raises(JSONPathRecursionError):
        env.findall(query, data)


def test_low_recursion_limit() -> None:
    class MockEnv(JSONPathEnvironment):
        max_recursion_depth = 3

    env = MockEnv()
    query = "$..a"
    data = {"foo": [{"bar": [1, 2, 3]}]}

    with pytest.raises(JSONPathRecursionError):
        env.findall(query, data)
