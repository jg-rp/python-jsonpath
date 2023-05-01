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
        path="$.some[?type(@.thing) == 'string']",
        data={"some": [{"thing": "foo"}]},
        want=[{"thing": "foo"}],
    ),
    Case(
        description="not a string",
        path="$.some[?type(@.thing) == 'string']",
        data={"some": [{"thing": 1}]},
        want=[],
    ),
    Case(
        description="type of undefined",
        path="$.some[?type(@.other) == 'undefined']",  # things without `other`
        data={"some": [{"thing": "foo"}]},
        want=[{"thing": "foo"}],
    ),
    Case(
        description="type of None",
        path="$.some[?type(@.thing) == 'null']",
        data={"some": [{"thing": None}]},
        want=[{"thing": None}],
    ),
    Case(
        description="type of array-like",
        path="$.some[?type(@.thing) == 'array']",
        data={"some": [{"thing": [1, 2, 3]}]},
        want=[{"thing": [1, 2, 3]}],
    ),
    Case(
        description="type of mapping",
        path="$.some[?type(@.thing) == 'object']",
        data={"some": [{"thing": {"other": 1}}]},
        want=[{"thing": {"other": 1}}],
    ),
    Case(
        description="type of bool",
        path="$.some[?type(@.thing) == 'boolean']",
        data={"some": [{"thing": True}]},
        want=[{"thing": True}],
    ),
    Case(
        description="type of int",
        path="$.some[?type(@.thing) == 'number']",
        data={"some": [{"thing": 1}]},
        want=[{"thing": 1}],
    ),
    Case(
        description="type of float",
        path="$.some[?type(@.thing) == 'number']",
        data={"some": [{"thing": 1.1}]},
        want=[{"thing": 1.1}],
    ),
    Case(
        description="none of the above",
        path="$.some[?type(@.thing) == 'object']",
        data={"some": [{"thing": SOME_OBJECT}]},
        want=[{"thing": SOME_OBJECT}],
    ),
]


@pytest.fixture()
def env() -> JSONPathEnvironment:
    return JSONPathEnvironment()


@pytest.mark.parametrize("case", TEST_CASES, ids=operator.attrgetter("description"))
def test_typeof_function(env: JSONPathEnvironment, case: Case) -> None:
    path = env.compile(case.path)
    assert path.findall(case.data) == case.want


@pytest.mark.parametrize("case", TEST_CASES, ids=operator.attrgetter("description"))
def test_typeof_function_async(env: JSONPathEnvironment, case: Case) -> None:
    path = env.compile(case.path)

    async def coro() -> List[object]:
        return await path.findall_async(case.data)

    assert asyncio.run(coro()) == case.want


# TODO: test single_number_type is False
