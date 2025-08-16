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

from jsonpath import JSONPathEnvironment
from jsonpath import JSONPathError
from jsonpath import NodeList


@dataclass
class Case:
    name: str
    selector: str
    document: Union[Mapping[str, Any], Sequence[Any], None] = None
    result: Any = None
    results: Optional[List[Any]] = None
    result_paths: Optional[List[str]] = None
    results_paths: Optional[List[List[str]]] = None
    invalid_selector: Optional[bool] = None
    tags: List[str] = field(default_factory=list)


SKIP = {
    # "filter, equals number, invalid no int digit": "expected behavior policy",
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
    # "filter, true, incorrectly capitalized": "flexible literal policy",
    # "filter, false, incorrectly capitalized": "flexible literal policy",
    # "filter, null, incorrectly capitalized": "flexible literal policy",
    "name selector, double quotes, single high surrogate": "expected behavior policy",
    "name selector, double quotes, single low surrogate": "expected behavior policy",
    "name selector, double quotes, high high surrogate": "expected behavior policy",
    "name selector, double quotes, low low surrogate": "expected behavior policy",
    "name selector, double quotes, surrogate non-surrogate": "expected behavior policy",
    "name selector, double quotes, non-surrogate surrogate": "expected behavior policy",
    "name selector, double quotes, surrogate supplementary": "expected behavior policy",
    "name selector, double quotes, supplementary surrogate": "expected behavior policy",
}

# CTS test that will only pass if the third party `regex` package is installed.
REGEX_ONLY = {
    "functions, match, filter, match function, unicode char class, uppercase",
    "functions, match, filter, match function, unicode char class negated, uppercase",
    "functions, search, filter, search function, unicode char class, uppercase",
    "functions, search, filter, search function, unicode char class negated, uppercase",
}

# TODO: Test compliance without strict mode. Assert expected failures.
# TODO: Test runner in `no-regexp` env


def cases() -> List[Case]:
    with open("tests/cts/cts.json", encoding="utf8") as fd:
        data = json.load(fd)
    return [Case(**case) for case in data["tests"]]


def valid_cases() -> List[Case]:
    return [case for case in cases() if not case.invalid_selector]


def invalid_cases() -> List[Case]:
    return [case for case in cases() if case.invalid_selector]


@pytest.fixture()
def env() -> JSONPathEnvironment:
    return JSONPathEnvironment(strict=True)


@pytest.mark.parametrize("case", valid_cases(), ids=operator.attrgetter("name"))
def test_compliance(env: JSONPathEnvironment, case: Case) -> None:
    if not env.regex_available and case.name in REGEX_ONLY:
        pytest.skip(reason="requires regex package")

    if case.name in SKIP:
        pytest.skip(reason=SKIP[case.name])

    assert case.document is not None
    nodes = NodeList(env.finditer(case.selector, case.document))

    if case.results is not None:
        assert case.results_paths is not None
        assert nodes.values() in case.results
        assert nodes.paths() in case.results_paths
    else:
        assert case.result_paths is not None
        assert nodes.values() == case.result
        assert nodes.paths() == case.result_paths


@pytest.mark.parametrize("case", valid_cases(), ids=operator.attrgetter("name"))
def test_compliance_async(env: JSONPathEnvironment, case: Case) -> None:
    if not env.regex_available and case.name in REGEX_ONLY:
        pytest.skip(reason="requires regex package")

    if case.name in SKIP:
        pytest.skip(reason=SKIP[case.name])

    async def coro() -> NodeList:
        assert case.document is not None
        it = await env.finditer_async(case.selector, case.document)
        return NodeList([node async for node in it])

    nodes = asyncio.run(coro())

    if case.results is not None:
        assert case.results_paths is not None
        assert nodes.values() in case.results
        assert nodes.paths() in case.results_paths
    else:
        assert case.result_paths is not None
        assert nodes.values() == case.result
        assert nodes.paths() == case.result_paths


@pytest.mark.parametrize("case", invalid_cases(), ids=operator.attrgetter("name"))
def test_invalid_selectors(env: JSONPathEnvironment, case: Case) -> None:
    if case.name in SKIP:
        pytest.skip(reason=SKIP[case.name])

    with pytest.raises(JSONPathError):
        env.compile(case.selector)
