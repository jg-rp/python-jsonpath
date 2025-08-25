import asyncio
import json
import operator

import pytest

from jsonpath import JSONPathEnvironment
from jsonpath import JSONPathSyntaxError
from jsonpath import NodeList

from ._cts_case import Case


@pytest.fixture()
def env() -> JSONPathEnvironment:
    return JSONPathEnvironment(strict=False)


with open("tests/undefined.json", encoding="utf8") as fd:
    data = [Case(**case) for case in json.load(fd)["tests"]]


@pytest.mark.parametrize("case", data, ids=operator.attrgetter("name"))
def test_undefined_keyword(env: JSONPathEnvironment, case: Case) -> None:
    assert case.document is not None
    nodes = NodeList(env.finditer(case.selector, case.document))
    case.assert_nodes(nodes)


@pytest.mark.parametrize("case", data, ids=operator.attrgetter("name"))
def test_undefined_keyword_async(env: JSONPathEnvironment, case: Case) -> None:
    async def coro() -> NodeList:
        assert case.document is not None
        it = await env.finditer_async(case.selector, case.document)
        return NodeList([node async for node in it])

    nodes = asyncio.run(coro())
    case.assert_nodes(nodes)


@pytest.mark.parametrize("case", data, ids=operator.attrgetter("name"))
def test_comparison_to_undefined_fails_in_strict_mode(case: Case) -> None:
    env = JSONPathEnvironment(strict=True)

    with pytest.raises(JSONPathSyntaxError):
        env.compile(case.selector)
