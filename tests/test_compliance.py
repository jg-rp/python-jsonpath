"""Test Python JSONPath against the JSONPath Compliance Test Suite.

The CTS is a submodule located in /tests/cts. After a git clone, run
`git submodule update --init` from the root of the repository.
"""

import asyncio
import json
import operator
from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import List
from typing import Mapping
from typing import Optional
from typing import Sequence
from typing import Union

import pytest

import jsonpath


@dataclass
class Case:
    name: str
    selector: str
    document: Union[Mapping[str, Any], Sequence[Any], None] = None
    result: Any = None
    results: Optional[List[Any]] = None
    invalid_selector: Optional[bool] = None
    tags: List[str] = field(default_factory=list)


SKIP = {
    "basic, no leading whitespace": "flexible whitespace policy",
    "basic, no trailing whitespace": "flexible whitespace policy",
    "basic, bald descendant segment": "almost has a consensus",
    "filter, index segment on object, selects nothing": "flexible selector policy",
    "functions, match, dot matcher on \\u2028": "standard library re policy",
    "functions, match, dot matcher on \\u2029": "standard library re policy",
    "functions, search, dot matcher on \\u2028": "standard library re policy",
    "functions, search, dot matcher on \\u2029": "standard library re policy",
    "functions, match, filter, match function, unicode char class, uppercase": "\\p not supported",  # noqa: E501
    "functions, match, filter, match function, unicode char class negated, uppercase": "\\P not supported",  # noqa: E501
    "functions, search, filter, search function, unicode char class, uppercase": "\\p not supported",  # noqa: E501
    "functions, search, filter, search function, unicode char class negated, uppercase": "\\P not supported",  # noqa: E501
    "filter, equals number, decimal fraction, no fractional digit": "expected behavior policy",  # noqa: E501
    "filter, equals number, decimal fraction, no int digit": "expected behavior policy",
    "filter, equals number, invalid no int digit": "expected behavior policy",
    "filter, equals number, invalid 00": "expected behavior policy",
    "filter, equals number, invalid leading 0": "expected behavior policy",
    "filter, equals number, invalid no fractional digit": "expected behavior policy",
    "filter, equals number, invalid no fractional digit e": "expected behavior policy",
    "slice selector, start, leading 0": "expected behavior policy",
    "slice selector, start, -0": "expected behavior policy",
    "slice selector, start, leading -0": "expected behavior policy",
    "slice selector, end, leading 0": "expected behavior policy",
    "slice selector, end, minus space": "expected behavior policy",
    "slice selector, end, -0": "expected behavior policy",
    "slice selector, end, leading -0": "expected behavior policy",
    "slice selector, step, leading 0": "expected behavior policy",
    "slice selector, step, minus space": "expected behavior policy",
    "slice selector, step, -0": "expected behavior policy",
    "slice selector, step, leading -0": "expected behavior policy",
    "filter, true, incorrectly capitalized": "flexible literal policy",
    "filter, false, incorrectly capitalized": "flexible literal policy",
    "filter, null, incorrectly capitalized": "flexible literal policy",
    "name selector, double quotes, single high surrogate": "expected behavior policy",
    "name selector, double quotes, single low surrogate": "expected behavior policy",
    "name selector, double quotes, high high surrogate": "expected behavior policy",
    "name selector, double quotes, low low surrogate": "expected behavior policy",
    "name selector, double quotes, surrogate non-surrogate": "expected behavior policy",
    "name selector, double quotes, non-surrogate surrogate": "expected behavior policy",
    "name selector, double quotes, surrogate supplementary": "expected behavior policy",
    "name selector, double quotes, supplementary surrogate": "expected behavior policy",
    "whitespace, selectors, space between dot and name": "flexible whitespace policy",  # noqa: E501
    "whitespace, selectors, newline between dot and name": "flexible whitespace policy",  # noqa: E501
    "whitespace, selectors, tab between dot and name": "flexible whitespace policy",  # noqa: E501
    "whitespace, selectors, return between dot and name": "flexible whitespace policy",  # noqa: E501
    "whitespace, selectors, space between recursive descent and name": "flexible whitespace policy",  # noqa: E501
    "whitespace, selectors, newline between recursive descent and name": "flexible whitespace policy",  # noqa: E501
    "whitespace, selectors, tab between recursive descent and name": "flexible whitespace policy",  # noqa: E501
    "whitespace, selectors, return between recursive descent and name": "flexible whitespace policy",  # noqa: E501
}


def cases() -> List[Case]:
    with open("tests/cts/cts.json", encoding="utf8") as fd:
        data = json.load(fd)
    return [Case(**case) for case in data["tests"]]


def valid_cases() -> List[Case]:
    return [case for case in cases() if not case.invalid_selector]


def invalid_cases() -> List[Case]:
    return [case for case in cases() if case.invalid_selector]


@pytest.mark.parametrize("case", valid_cases(), ids=operator.attrgetter("name"))
def test_compliance(case: Case) -> None:
    if case.name in SKIP:
        pytest.skip(reason=SKIP[case.name])

    assert case.document is not None
    rv = jsonpath.findall(case.selector, case.document)

    if case.results is not None:
        assert rv in case.results
    else:
        assert rv == case.result


@pytest.mark.parametrize("case", valid_cases(), ids=operator.attrgetter("name"))
def test_compliance_async(case: Case) -> None:
    if case.name in SKIP:
        pytest.skip(reason=SKIP[case.name])

    async def coro() -> List[object]:
        assert case.document is not None
        return await jsonpath.findall_async(case.selector, case.document)

    if case.results is not None:
        assert asyncio.run(coro()) in case.results
    else:
        assert asyncio.run(coro()) == case.result


@pytest.mark.parametrize("case", invalid_cases(), ids=operator.attrgetter("name"))
def test_invalid_selectors(case: Case) -> None:
    if case.name in SKIP:
        pytest.skip(reason=SKIP[case.name])

    with pytest.raises(jsonpath.JSONPathError):
        jsonpath.compile(case.selector)
