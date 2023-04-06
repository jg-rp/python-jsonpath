import asyncio
import dataclasses
import operator
from typing import Any
from typing import List
from typing import Mapping
from typing import Sequence
from typing import Union

import pytest

from jsonpath import JSONPathEnvironment


@dataclasses.dataclass
class Case:
    description: str
    path: str
    data: Union[Sequence[Any], Mapping[str, Any]]
    want: Union[Sequence[Any], Mapping[str, Any]]


TEST_CASES = [
    Case(
        description="match a regex",
        path="$.some[?(@.thing =~ /fo[a-z]/)]",
        data={"some": [{"thing": "foo"}]},
        want=[{"thing": "foo"}],
    ),
    Case(
        description="regex with no match",
        path="$.some[?(@.thing =~ /fo[a-z]/)]",
        data={"some": [{"thing": "foO"}]},
        want=[],
    ),
    Case(
        description="case insensitive match",
        path="$.some[?(@.thing =~ /fo[a-z]/i)]",
        data={"some": [{"thing": "foO"}]},
        want=[{"thing": "foO"}],
    ),
]


@pytest.fixture()
def env() -> JSONPathEnvironment:
    return JSONPathEnvironment()


@pytest.mark.parametrize("case", TEST_CASES, ids=operator.attrgetter("description"))
def test_filter_regex(env: JSONPathEnvironment, case: Case) -> None:
    path = env.compile(case.path)
    assert path.findall(case.data) == case.want


@pytest.mark.parametrize("case", TEST_CASES, ids=operator.attrgetter("description"))
def test_filter_regex_async(env: JSONPathEnvironment, case: Case) -> None:
    path = env.compile(case.path)

    async def coro() -> List[object]:
        return await path.findall_async(case.data)

    assert asyncio.run(coro()) == case.want
