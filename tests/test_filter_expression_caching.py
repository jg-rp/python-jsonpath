"""Filter expression caching test cases."""
import dataclasses
import operator
from unittest import mock

import pytest

import jsonpath
from jsonpath import JSONPath
from jsonpath import JSONPathEnvironment
from jsonpath.filter import BooleanExpression
from jsonpath.filter import CachingFilterExpression
from jsonpath.filter import FilterContextPath
from jsonpath.filter import FilterExpression
from jsonpath.filter import InfixExpression
from jsonpath.filter import RootPath
from jsonpath.filter import SelfPath
from jsonpath.filter import is_volatile
from jsonpath.selectors import Filter as FilterSelector


@dataclasses.dataclass
class Case:
    description: str
    path: str
    want: bool


TEST_CASES = [
    Case(
        description="boolean self path",
        path="$some.thing[?@.foo]",
        want=True,
    ),
    Case(
        description="infix left self path",
        path="$some.thing[?@.foo > $.bar]",
        want=True,
    ),
    Case(
        description="infix left self path",
        path="$some.thing[?$.bar == @.foo]",
        want=True,
    ),
    Case(
        description="nested filter self path",
        path="$some.thing[?$.bar[?@.foo > 1]]",
        want=True,
    ),
    Case(
        description="self path as filter function argument",
        path="$some.thing[?match(@.foo, '^bar.+')]",
        want=True,
    ),
    Case(
        description="boolean root path",
        path="$some.thing[?$.foo]",
        want=False,
    ),
]


@pytest.mark.parametrize("case", TEST_CASES, ids=operator.attrgetter("description"))
def test_is_volatile(case: Case) -> None:
    path = jsonpath.compile(case.path)
    assert isinstance(path, jsonpath.JSONPath)

    filter_selectors = [
        selector for selector in path.selectors if isinstance(selector, FilterSelector)
    ]

    assert len(filter_selectors) == 1
    assert is_volatile(filter_selectors[0].expression) is case.want


def test_cache_root_path() -> None:
    """Test that we wrap root paths in a caching node."""
    env = JSONPathEnvironment()
    path = env.compile("$.some[?@.a < $.thing].a")
    assert isinstance(path, JSONPath)
    filter_selector = path.selectors[1]
    assert isinstance(filter_selector, FilterSelector)

    # The original expression tree without caching nodes.
    expr: FilterExpression = filter_selector.expression
    assert isinstance(expr, BooleanExpression)
    expr = expr.expression
    assert isinstance(expr, InfixExpression)
    assert isinstance(expr.left, SelfPath)
    assert isinstance(expr.right, RootPath)

    # A caching copy of the original expression tree.
    expr = filter_selector.expression.cache_tree()
    assert isinstance(expr, BooleanExpression)
    expr = expr.expression
    assert isinstance(expr, InfixExpression)
    assert isinstance(expr.left, SelfPath)
    assert isinstance(expr.right, CachingFilterExpression)
    assert isinstance(expr.right._expr, RootPath)  # noqa: SLF001


def test_root_path_cache() -> None:
    """Test that we evaluate root paths once when caching is enabled."""
    env = JSONPathEnvironment(filter_caching=True)
    data = {"some": [{"a": 1}, {"a": 99}, {"a": 2}, {"a": 3}]}
    with mock.patch(
        "jsonpath.filter.RootPath.evaluate", return_value=10
    ) as mock_root_path:
        path = env.compile("$.some[?@.a < $.thing].a")
        rv = path.findall(data)
        assert rv == [1, 2, 3]
        assert mock_root_path.call_count == 1


def test_root_path_no_cache() -> None:
    """Test that we evaluate root paths once for each match when caching is disabled."""
    env = JSONPathEnvironment(filter_caching=False)
    data = {"some": [{"a": 1}, {"a": 99}, {"a": 2}, {"a": 3}]}
    with mock.patch(
        "jsonpath.filter.RootPath.evaluate", return_value=10
    ) as mock_root_path:
        path = env.compile("$.some[?@.a < $.thing].a")
        rv = path.findall(data)
        assert rv == [1, 2, 3]
        assert mock_root_path.call_count == 4  # noqa: PLR2004


def test_cache_context_path() -> None:
    """Test that we wrap filter context paths in a caching node."""
    env = JSONPathEnvironment()
    path = env.compile("$.some[?_.thing > @.a].a")
    assert isinstance(path, JSONPath)
    filter_selector = path.selectors[1]
    assert isinstance(filter_selector, FilterSelector)

    # The original expression tree without caching nodes.
    expr: FilterExpression = filter_selector.expression
    assert isinstance(expr, BooleanExpression)
    expr = expr.expression
    assert isinstance(expr, InfixExpression)
    assert isinstance(expr.left, FilterContextPath)
    assert isinstance(expr.right, SelfPath)

    # A caching copy of the original expression tree.
    expr = filter_selector.expression.cache_tree()
    assert isinstance(expr, BooleanExpression)
    expr = expr.expression
    assert isinstance(expr, InfixExpression)
    assert isinstance(expr.left, CachingFilterExpression)
    assert isinstance(expr.left._expr, FilterContextPath)  # noqa: SLF001
    assert isinstance(expr.right, SelfPath)


def test_context_path_cache() -> None:
    """Test that we evaluate filter context paths once when caching is enabled."""
    env = JSONPathEnvironment(filter_caching=True)
    data = {"some": [{"a": 1}, {"a": 99}, {"a": 2}, {"a": 3}]}
    with mock.patch(
        "jsonpath.filter.FilterContextPath.evaluate", return_value=10
    ) as mock_root_path:
        path = env.compile("$.some[?_.thing > @.a].a")
        rv = path.findall(data)
        assert rv == [1, 2, 3]
        assert mock_root_path.call_count == 1


def test_context_path_no_cache() -> None:
    """Test that we evaluate context path for each match when caching is disabled."""
    env = JSONPathEnvironment(filter_caching=False)
    data = {"some": [{"a": 1}, {"a": 99}, {"a": 2}, {"a": 3}]}
    with mock.patch(
        "jsonpath.filter.FilterContextPath.evaluate", return_value=10
    ) as mock_root_path:
        path = env.compile("$.some[?_.thing > @.a].a")
        rv = path.findall(data)
        assert rv == [1, 2, 3]
        assert mock_root_path.call_count == 4  # noqa: PLR2004


def test_cache_expires() -> None:
    """Test that the cache expires between calls to findall/finditer."""
    env = JSONPathEnvironment(filter_caching=True)
    path = env.compile("$.some.thing[?@.other < $.foo]")
    some_data = {
        "some": {"thing": [{"other": 1}, {"other": 2}, {"other": 3}]},
        "foo": 10,
    }
    other_data = {
        "some": {"thing": [{"other": 1}, {"other": 2}, {"other": 3}]},
        "foo": 1,
    }
    assert path.findall(some_data) == [{"other": 1}, {"other": 2}, {"other": 3}]
    assert path.findall(other_data) == []


def test_cache_logical_infix() -> None:
    # TODO:
    pass
