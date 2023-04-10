"""Test Python JSONPath against the JSONPath Compliance Test Suite.

Assumes a version of the test suite is available in the current  working
directory as "cts.json".

See https://github.com/jsonpath-standard/jsonpath-compliance-test-suite.

We've deliberately named this file so as to exclude it when running `pytest`
or `hatch run test`. Target it specifically using `pytest tests/compliance.py`.
"""
import asyncio
import json
import operator
import unittest
from dataclasses import dataclass
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
    invalid_selector: Optional[bool] = None


SKIP = {
    "no leading whitespace": "flexible whitespace policy",
    "no trailing whitespace": "flexible whitespace policy",
    "bald descendant segment": "alost has a consensus",
    "name selector, double quotes, invalid escaped single quote": "TODO",
    "name selector, double quotes, incomplete escape": "TODO",
    "name selector, single quotes, invalid escaped double quote": "TODO",
    "name selector, single quotes, incomplete escape": "TODO",
    "index selector, leading 0": "TODO",
    "index selector, leading -0": "TODO",
    "filter, non-singular query in comparison, slice": "TODO",
    "filter, non-singular query in comparison, all children": "TODO",
    "filter, non-singular query in comparison, descendants": "TODO",
    "filter, non-singular query in comparison, combined": "TODO",
    "filter, length function, result must be compared": "TODO",
    "filter, count function, non-array/string arg": "TODO",
    "filter, count function, result must be compared": "TODO",
    "filter, match function, result cannot be compared": "TODO",
    "filter, search function, result cannot be compared": "TODO",
    "filter, value function, result must be compared": "TODO",
}


def cases() -> List[Case]:
    with open("cts.json", encoding="utf8") as fd:
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

    test_case = unittest.TestCase()
    rv = jsonpath.findall(case.selector, case.document)
    test_case.assertCountEqual(rv, case.result)  # noqa: PT009


@pytest.mark.parametrize("case", valid_cases(), ids=operator.attrgetter("name"))
def test_compliance_async(case: Case) -> None:
    if case.name in SKIP:
        pytest.skip(reason=SKIP[case.name])

    async def coro() -> List[object]:
        assert case.document is not None
        return await jsonpath.findall_async(case.selector, case.document)

    test_case = unittest.TestCase()
    test_case.assertCountEqual(asyncio.run(coro()), case.result)  # noqa: PT009


@pytest.mark.parametrize("case", invalid_cases(), ids=operator.attrgetter("name"))
def test_invalid_selectors(case: Case) -> None:
    if case.name in SKIP:
        pytest.skip(reason=SKIP[case.name])

    with pytest.raises(jsonpath.JSONPathError):
        jsonpath.compile(case.selector)
