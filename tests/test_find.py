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
        description="slice a mapping",
        path="$.some[0:4]",
        data={"some": {"thing": "else"}},
        want=[],
    ),
    Case(
        description="keys from a mapping",
        path="$.some[~]",
        data={"some": {"thing": "else"}},
        want=["thing"],
    ),
    Case(
        description="keys from a sequence",
        path="$.some.~",
        data={"some": ["thing", "else"]},
        want=[],
    ),
    Case(
        description="match key pattern",
        path="$.some[?match(#, 'thing[0-9]+')]",
        data={
            "some": {
                "thing1": {"foo": 1},
                "thing2": {"foo": 2},
                "other": {"foo": 3},
            }
        },
        want=[{"foo": 1}, {"foo": 2}],
    ),
    Case(
        description="filter current key, array data",
        path="$.abc[?(# >= 1)]",
        data={"abc": [1, 2, 3], "def": [4, 5], "abx": [6], "aby": []},
        want=[2, 3],
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
        description="recurse object keys",
        path="$..~",
        data={"some": {"thing": "else", "foo": {"bar": "baz"}}},
        want=["some", "thing", "foo", "bar"],
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
        description="array contains literal",
        path="$[?@.a contains 'foo']",
        data=[{"a": ["foo", "bar"]}, {"a": ["bar"]}],
        want=[
            {
                "a": ["foo", "bar"],
            }
        ],
    ),
    Case(
        description="object contains literal",
        path="$[?@.a contains 'foo']",
        data=[{"a": {"foo": "bar"}}, {"a": {"bar": "baz"}}],
        want=[
            {
                "a": {"foo": "bar"},
            }
        ],
    ),
    Case(
        description="literal in array",
        path="$[?'foo' in @.a]",
        data=[{"a": ["foo", "bar"]}, {"a": ["bar"]}],
        want=[
            {
                "a": ["foo", "bar"],
            }
        ],
    ),
    Case(
        description="literal in object",
        path="$[?'foo' in @.a]",
        data=[{"a": {"foo": "bar"}}, {"a": {"bar": "baz"}}],
        want=[
            {
                "a": {"foo": "bar"},
            }
        ],
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
