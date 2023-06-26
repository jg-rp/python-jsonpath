"""Test that we can traverse filter expression trees."""
import dataclasses
import operator

import pytest

import jsonpath
from jsonpath.filter import FilterExpression
from jsonpath.filter import walk
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


def is_volatile(expr: FilterExpression) -> bool:
    return any(expr.volatile for expr in walk(expr))


@pytest.mark.parametrize("case", TEST_CASES, ids=operator.attrgetter("description"))
def test_is_volatile(case: Case) -> None:
    path = jsonpath.compile(case.path)
    assert isinstance(path, jsonpath.JSONPath)

    filter_selectors = [
        selector for selector in path.selectors if isinstance(selector, FilterSelector)
    ]

    assert len(filter_selectors) == 1
    assert is_volatile(filter_selectors[0].expression) is case.want
