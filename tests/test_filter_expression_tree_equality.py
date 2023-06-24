"""Test cases for copying and testing filter expressions for equality."""
import copy

import jsonpath
from jsonpath.selectors import Filter as FilterSelector


def test_copy_filter_expression() -> None:
    path = jsonpath.compile("$some.thing[?@.foo > $.bar && 1 < 2.2]")
    assert isinstance(path, jsonpath.JSONPath)

    filter_selectors = [
        selector for selector in path.selectors if isinstance(selector, FilterSelector)
    ]

    assert len(filter_selectors) == 1
    expression = filter_selectors[0].expression
    copied_expression = copy.deepcopy(expression)
    assert expression == copied_expression
    assert expression is not copied_expression

    # copied_expression.expression = CachingBooleanExpression(expression)
    # assert expression != copied_expression
