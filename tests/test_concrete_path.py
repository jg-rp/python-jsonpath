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
from jsonpath import JSONPathMatch


@dataclasses.dataclass
class Case:
    description: str
    path: str
    data: Union[Sequence[Any], Mapping[str, Any]]
    want: List[str]


TEST_CASES = [
    Case(
        description="normalized negative index",
        path="$.a[-2]",
        data={"a": [1, 2, 3, 4, 5]},
        want=["$['a'][3]"],
    ),
    Case(
        description="normalized reverse slice",
        path="$.a[3:0:-1]",
        data={"a": [1, 2, 3, 4, 5]},
        want=["$['a'][3]", "$['a'][2]", "$['a'][1]"],
    ),
]


@pytest.fixture()
def env() -> JSONPathEnvironment:
    return JSONPathEnvironment()


@pytest.mark.parametrize("case", TEST_CASES, ids=operator.attrgetter("description"))
def test_find(env: JSONPathEnvironment, case: Case) -> None:
    path = env.compile(case.path)
    matches = list(path.finditer(case.data))
    assert len(matches) == len(case.want)
    for match, want in zip(matches, case.want):  # noqa: B905
        assert match.path == want


@pytest.mark.parametrize("case", TEST_CASES, ids=operator.attrgetter("description"))
def test_find_async(env: JSONPathEnvironment, case: Case) -> None:
    path = env.compile(case.path)

    async def coro() -> List[JSONPathMatch]:
        matches = await path.finditer_async(case.data)
        return [match async for match in matches]

    matches = asyncio.run(coro())
    assert len(matches) == len(case.want)
    for match, want in zip(matches, case.want):  # noqa: B905
        assert match.path == want
