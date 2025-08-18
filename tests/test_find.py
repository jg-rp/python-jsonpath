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

# TODO: move the rest of these test cases and delete me


@dataclasses.dataclass
class Case:
    description: str
    path: str
    data: Union[Sequence[Any], Mapping[str, Any]]
    want: Union[Sequence[Any], Mapping[str, Any]]


TEST_CASES = [
    Case(
        description="slice a mapping",
        path="$.some[0:4]",
        data={"some": {"thing": "else"}},
        want=[],
    ),
    Case(
        description="select root value using pseudo root",
        path="^[?@.some.thing > 7]",
        data={"some": {"thing": 42}},
        want=[{"some": {"thing": 42}}],
    ),
    Case(
        description="pseudo root in a filter query",
        path="^[?@.some.thing > value(^.*.num)]",
        data={"some": {"thing": 42}, "num": 7},
        want=[{"some": {"thing": 42}, "num": 7}],
    ),
    Case(
        description="logical expr existence tests",
        path="$[?@.a && @.b]",
        data=[{"a": True, "b": False}],
        want=[{"a": True, "b": False}],
    ),
    Case(
        description="logical expr existence tests, alternate and",
        path="$[?@.a and @.b]",
        data=[{"a": True, "b": False}],
        want=[{"a": True, "b": False}],
    ),
    Case(
        description="quoted reserved word, and",
        path="$['and']",
        data={"and": [1, 2, 3]},
        want=[[1, 2, 3]],
    ),
    Case(
        description="quoted reserved word, or",
        path="$['or']",
        data={"or": [1, 2, 3]},
        want=[[1, 2, 3]],
    ),
]


@pytest.fixture()
def env() -> JSONPathEnvironment:
    return JSONPathEnvironment()


@pytest.mark.parametrize("case", TEST_CASES, ids=operator.attrgetter("description"))
def test_find(env: JSONPathEnvironment, case: Case) -> None:
    path = env.compile(case.path)
    assert path.findall(case.data) == case.want


@pytest.mark.parametrize("case", TEST_CASES, ids=operator.attrgetter("description"))
def test_find_async(env: JSONPathEnvironment, case: Case) -> None:
    path = env.compile(case.path)

    async def coro() -> List[object]:
        return await path.findall_async(case.data)

    assert asyncio.run(coro()) == case.want
