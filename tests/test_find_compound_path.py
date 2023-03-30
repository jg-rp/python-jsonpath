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
        description="union of two paths",
        path="$.some | $.thing",
        data={"some": [1, 2, 3], "thing": [4, 5, 6], "other": ["a", "b", "c"]},
        want=[[1, 2, 3], [4, 5, 6]],
    ),
    Case(
        description="union of three paths",
        path="$.some | $.thing | $.other",
        data={"some": [1, 2, 3], "thing": [4, 5, 6], "other": ["a", "b", "c"]},
        want=[[1, 2, 3], [4, 5, 6], ["a", "b", "c"]],
    ),
    Case(
        description="intersection of two paths with no common items",
        path="$.some & $.thing",
        data={"some": [1, 2, 3], "thing": [4, 5, 6], "other": ["a", "b", "c"]},
        want=[],
    ),
    Case(
        description="intersection of two paths with common item",
        path="$.some & $.thing",
        data={"some": [1, 2, 3], "thing": [1, 2, 3], "other": ["a", "b", "c"]},
        want=[[1, 2, 3]],
    ),
    Case(
        description="intersection then union",
        path="$.some & $.thing | $.other",
        data={"some": [1, 2, 3], "thing": [1, 2, 3], "other": ["a", "b", "c"]},
        want=[[1, 2, 3], ["a", "b", "c"]],
    ),
]


@pytest.fixture()
def env() -> JSONPathEnvironment:
    return JSONPathEnvironment()


@pytest.mark.parametrize("case", TEST_CASES, ids=operator.attrgetter("description"))
def test_find_compound_path(env: JSONPathEnvironment, case: Case) -> None:
    path = env.compile(case.path)
    assert path.findall(case.data) == case.want
    assert [match.obj for match in path.finditer(case.data)] == case.want


@pytest.mark.parametrize("case", TEST_CASES, ids=operator.attrgetter("description"))
def test_find_compound_path_async(env: JSONPathEnvironment, case: Case) -> None:
    path = env.compile(case.path)

    async def coro() -> List[object]:
        return await path.findall_async(case.data)

    async def iter_coro() -> List[object]:
        return [match.obj async for match in await path.finditer_async(case.data)]

    assert asyncio.run(coro()) == case.want
    assert asyncio.run(iter_coro()) == case.want
