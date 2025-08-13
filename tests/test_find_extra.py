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
        description="keys from an object",
        path="$.some[~]",
        data={"some": {"other": "foo", "thing": "bar"}},
        want=["other", "thing"],
    ),
    Case(
        description="shorthand keys from an object",
        path="$.some.~",
        data={"some": {"other": "foo", "thing": "bar"}},
        want=["other", "thing"],
    ),
    Case(
        description="keys from an array",
        path="$.some[~]",
        data={"some": ["other", "thing"]},
        want=[],
    ),
    Case(
        description="shorthand keys from an array",
        path="$.some.~",
        data={"some": ["other", "thing"]},
        want=[],
    ),
    Case(
        description="recurse object keys",
        path="$..~",
        data={"some": {"thing": "else", "foo": {"bar": "baz"}}},
        want=["some", "thing", "foo", "bar"],
    ),
    Case(
        description="current key of an object",
        path="$.some[?match(#, '^b.*')]",
        data={"some": {"foo": "a", "bar": "b", "baz": "c", "qux": "d"}},
        want=["b", "c"],
    ),
    Case(
        description="current key of an array",
        path="$.some[?# > 1]",
        data={"some": ["other", "thing", "foo", "bar"]},
        want=["foo", "bar"],
    ),
    Case(
        description="filter keys from an object",
        path="$.some[~?match(@, '^b.*')]",
        data={"some": {"other": "foo", "thing": "bar"}},
        want=["thing"],
    ),
    Case(
        description="singular key from an object",
        path="$.some[~'other']",
        data={"some": {"other": "foo", "thing": "bar"}},
        want=["other"],
    ),
    Case(
        description="singular key from an object, does not exist",
        path="$.some[~'else']",
        data={"some": {"other": "foo", "thing": "bar"}},
        want=[],
    ),
    Case(
        description="singular key from an array",
        path="$.some[~'1']",
        data={"some": ["foo", "bar"]},
        want=[],
    ),
    Case(
        description="singular key from an object, shorthand",
        path="$.some.~other",
        data={"some": {"other": "foo", "thing": "bar"}},
        want=["other"],
    ),
    Case(
        description="recursive key from an object",
        path="$.some..[~'other']",
        data={"some": {"other": "foo", "thing": "bar", "else": {"other": "baz"}}},
        want=["other", "other"],
    ),
    Case(
        description="recursive key from an object, shorthand",
        path="$.some..~other",
        data={"some": {"other": "foo", "thing": "bar", "else": {"other": "baz"}}},
        want=["other", "other"],
    ),
    Case(
        description="recursive key from an object, does not exist",
        path="$.some..[~'nosuchthing']",
        data={"some": {"other": "foo", "thing": "bar", "else": {"other": "baz"}}},
        want=[],
    ),
    Case(
        description="object name from embedded singular query resolving to nothing",
        path="$.a[$.foo]",
        data={
            "a": {"j": [1, 2, 3], "p": {"q": [4, 5, 6]}},
            "b": ["j", "p", "q"],
            "c d": {"x": {"y": 1}},
        },
        want=[],
    ),
    Case(
        description="array index from embedded singular query resolving to nothing",
        path="$.b[$.foo]",
        data={
            "a": {"j": [1, 2, 3], "p": {"q": [4, 5, 6]}},
            "b": ["j", "p", "q"],
            "c d": {"x": {"y": 1}},
        },
        want=[],
    ),
    Case(
        description="array index from embedded singular query is not an int",
        path="$.b[$.a.z]",
        data={
            "a": {"j": [1, 2, 3], "p": {"q": [4, 5, 6]}, "z": "foo"},
            "b": ["j", "p", "q"],
            "c d": {"x": {"y": 1}},
        },
        want=[],
    ),
    Case(
        description="array index from embedded singular query is negative",
        path="$.b[$.a.z]",
        data={
            "a": {"j": [1, 2, 3], "p": {"q": [4, 5, 6]}, "z": -1},
            "b": ["j", "p", "q"],
            "c d": {"x": {"y": 1}},
        },
        want=["q"],
    ),
]


@pytest.fixture()
def env() -> JSONPathEnvironment:
    return JSONPathEnvironment()


@pytest.mark.parametrize("case", TEST_CASES, ids=operator.attrgetter("description"))
def test_find_extra(env: JSONPathEnvironment, case: Case) -> None:
    path = env.compile(case.path)
    assert path.findall(case.data) == case.want


@pytest.mark.parametrize("case", TEST_CASES, ids=operator.attrgetter("description"))
def test_find_extra_async(env: JSONPathEnvironment, case: Case) -> None:
    path = env.compile(case.path)

    async def coro() -> List[object]:
        return await path.findall_async(case.data)

    assert asyncio.run(coro()) == case.want
