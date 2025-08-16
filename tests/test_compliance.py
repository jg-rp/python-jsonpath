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

# CTS tests that are expected to fail when JSONPathEnvironment.strict is False.
XFAIL_INVALID = {
    "basic, no leading whitespace",
    "basic, no trailing whitespace",
    "filter, equals number, invalid 00",
    "filter, equals number, invalid leading 0",
    "filter, true, incorrectly capitalized",
    "filter, false, incorrectly capitalized",
    "filter, null, incorrectly capitalized",
    "name selector, double quotes, single high surrogate",
    "name selector, double quotes, single low surrogate",
    "name selector, double quotes, high high surrogate",
    "name selector, double quotes, low low surrogate",
    "name selector, double quotes, surrogate non-surrogate",
    "name selector, double quotes, non-surrogate surrogate",
    "name selector, double quotes, surrogate supplementary",
    "name selector, double quotes, supplementary surrogate",
}

XFAIL_VALID = {
    "filter, index segment on object, selects nothing",
}

# CTS test that will only pass if the third party `regex` package is installed.
REGEX_ONLY = {
    "functions, match, dot matcher on \\u2028",
    "functions, match, dot matcher on \\u2029",
    "functions, search, dot matcher on \\u2028",
    "functions, search, dot matcher on \\u2029",
    "functions, match, filter, match function, unicode char class, uppercase",
    "functions, match, filter, match function, unicode char class negated, uppercase",
    "functions, search, filter, search function, unicode char class, uppercase",
    "functions, search, filter, search function, unicode char class negated, uppercase",
}

# TODO: Test runner in `no-regexp` env


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


with open("tests/cts/cts.json", encoding="utf8") as fd:
    data = json.load(fd)

CASES = [Case(**case) for case in data["tests"]]


def valid_cases() -> List[Case]:
    return [case for case in CASES if not case.invalid_selector]


def invalid_cases() -> List[Case]:
    return [case for case in CASES if case.invalid_selector]


@pytest.fixture()
def env() -> JSONPathEnvironment:
    return JSONPathEnvironment(strict=True)


@pytest.mark.parametrize("case", valid_cases(), ids=operator.attrgetter("name"))
def test_compliance_strict(env: JSONPathEnvironment, case: Case) -> None:
    if not env.regex_available and case.name in REGEX_ONLY:
        pytest.skip(reason="requires regex package")

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
def test_compliance_async_strict(env: JSONPathEnvironment, case: Case) -> None:
    if not env.regex_available and case.name in REGEX_ONLY:
        pytest.skip(reason="requires regex package")

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
def test_invalid_selectors_strict(env: JSONPathEnvironment, case: Case) -> None:
    with pytest.raises(JSONPathError):
        env.compile(case.selector)


@pytest.mark.parametrize("case", valid_cases(), ids=operator.attrgetter("name"))
def test_compliance_lax(case: Case) -> None:
    env = JSONPathEnvironment(strict=False)

    if not env.regex_available and case.name in REGEX_ONLY:
        pytest.skip(reason="requires regex package")

    assert case.document is not None
    nodes = NodeList(env.finditer(case.selector, case.document))

    if case.results is not None:
        assert case.results_paths is not None

        if case.name in XFAIL_VALID:
            assert nodes.values() not in case.results
            assert nodes.paths() in case.results_paths
        else:
            assert nodes.values() in case.results
            assert nodes.paths() in case.results_paths
    else:
        assert case.result_paths is not None

        if case.name in XFAIL_VALID:
            assert nodes.values() != case.result
            assert nodes.paths() != case.result_paths
        else:
            assert nodes.values() == case.result
            assert nodes.paths() == case.result_paths


@pytest.mark.parametrize("case", invalid_cases(), ids=operator.attrgetter("name"))
def test_invalid_selectors_lax(case: Case) -> None:
    env = JSONPathEnvironment(strict=False)

    if case.name in XFAIL_INVALID:
        env.compile(case.selector)
    else:
        with pytest.raises(JSONPathError):
            env.compile(case.selector)
