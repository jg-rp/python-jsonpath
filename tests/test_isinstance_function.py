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


SOME_OBJECT = object()

TEST_CASES = [
    Case(
        description="type of a string",
        path="$.some[?is(@.thing, 'string')]",
        data={"some": [{"thing": "foo"}]},
        want=[{"thing": "foo"}],
    ),
    Case(
        description="not a string",
        path="$.some[?is(@.thing, 'string')]",
        data={"some": [{"thing": 1}]},
        want=[],
    ),
    Case(
        description="type of undefined",
        path="$.some[?is(@.other, 'undefined')]",  # things without `other`
        data={"some": [{"thing": "foo"}]},
        want=[{"thing": "foo"}],
    ),
    Case(
        description="type of None",
        path="$.some[?is(@.thing, 'null')]",
        data={"some": [{"thing": None}]},
        want=[{"thing": None}],
    ),
    Case(
        description="type of array-like",
        path="$.some[?is(@.thing, 'array')]",
        data={"some": [{"thing": [1, 2, 3]}]},
        want=[{"thing": [1, 2, 3]}],
    ),
    Case(
        description="type of mapping",
        path="$.some[?is(@.thing, 'object')]",
        data={"some": [{"thing": {"other": 1}}]},
        want=[{"thing": {"other": 1}}],
    ),
    Case(
        description="type of bool",
        path="$.some[?is(@.thing, 'boolean')]",
        data={"some": [{"thing": True}]},
        want=[{"thing": True}],
    ),
    Case(
        description="type of int",
        path="$.some[?is(@.thing, 'number')]",
        data={"some": [{"thing": 1}]},
        want=[{"thing": 1}],
    ),
    Case(
        description="type of float",
        path="$.some[?is(@.thing, 'number')]",
        data={"some": [{"thing": 1.1}]},
        want=[{"thing": 1.1}],
    ),
    Case(
        description="none of the above",
        path="$.some[?is(@.thing, 'object')]",
        data={"some": [{"thing": SOME_OBJECT}]},
        want=[{"thing": SOME_OBJECT}],
    ),
]


@pytest.fixture()
def env() -> JSONPathEnvironment:
    return JSONPathEnvironment()


@pytest.mark.parametrize("case", TEST_CASES, ids=operator.attrgetter("description"))
def test_isinstance_function(env: JSONPathEnvironment, case: Case) -> None:
    path = env.compile(case.path)
    assert path.findall(case.data) == case.want


@pytest.mark.parametrize("case", TEST_CASES, ids=operator.attrgetter("description"))
def test_isinstance_function_async(env: JSONPathEnvironment, case: Case) -> None:
    path = env.compile(case.path)

    async def coro() -> List[object]:
        return await path.findall_async(case.data)

    assert asyncio.run(coro()) == case.want
