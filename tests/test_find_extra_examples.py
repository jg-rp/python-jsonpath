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
    want_paths: List[str]


TEST_CASES = [
    Case(
        description="key selector, key of nested object",
        path="$.a[0].~c",
        data={
            "a": [{"b": "x", "c": "z"}, {"b": "y"}],
        },
        want=["c"],
        want_paths=["$['a'][0][~'c']"],
    ),
    Case(
        description="key selector, key does not exist",
        path="$.a[1].~c",
        data={
            "a": [{"b": "x", "c": "z"}, {"b": "y"}],
        },
        want=[],
        want_paths=[],
    ),
    Case(
        description="key selector, descendant, single quoted key",
        path="$..[~'b']",
        data={
            "a": [{"b": "x", "c": "z"}, {"b": "y"}],
        },
        want=["b", "b"],
        want_paths=["$['a'][0][~'b']", "$['a'][1][~'b']"],
    ),
    Case(
        description="key selector, descendant, double quoted key",
        path='$..[~"b"]',
        data={
            "a": [{"b": "x", "c": "z"}, {"b": "y"}],
        },
        want=["b", "b"],
        want_paths=["$['a'][0][~'b']", "$['a'][1][~'b']"],
    ),
    Case(
        description="keys selector, object key",
        path="$.a[0].~",
        data={
            "a": [{"b": "x", "c": "z"}, {"b": "y"}],
        },
        want=["b", "c"],
        want_paths=["$['a'][0][~'b']", "$['a'][0][~'c']"],
    ),
    Case(
        description="keys selector, array key",
        path="$.a.~",
        data={
            "a": [{"b": "x", "c": "z"}, {"b": "y"}],
        },
        want=[],
        want_paths=[],
    ),
    Case(
        description="keys selector, descendant keys",
        path="$..[~]",
        data={
            "a": [{"b": "x", "c": "z"}, {"b": "y"}],
        },
        want=["a", "b", "c", "b"],
        want_paths=["$[~'a']", "$['a'][0][~'b']", "$['a'][0][~'c']", "$['a'][1][~'b']"],
    ),
    Case(
        description="keys filter selector, conditionally select object keys",
        path="$.*[~?length(@) > 2]",
        data=[{"a": [1, 2, 3], "b": [4, 5]}, {"c": {"x": [1, 2]}}, {"d": [1, 2, 3]}],
        want=["a", "d"],
        want_paths=["$[0][~'a']", "$[2][~'d']"],
    ),
    Case(
        description="keys filter selector, existence test",
        path="$.*[~?@.x]",
        data=[{"a": [1, 2, 3], "b": [4, 5]}, {"c": {"x": [1, 2]}}, {"d": [1, 2, 3]}],
        want=["c"],
        want_paths=["$[1][~'c']"],
    ),
    Case(
        description="keys filter selector, keys from an array",
        path="$[~?(true == true)]",
        data=[{"a": [1, 2, 3], "b": [4, 5]}, {"c": {"x": [1, 2]}}, {"d": [1, 2, 3]}],
        want=[],
        want_paths=[],
    ),
    Case(
        description="current key identifier, match on object names",
        path="$[?match(#, '^ab.*') && length(@) > 0 ]",
        data={"abc": [1, 2, 3], "def": [4, 5], "abx": [6], "aby": []},
        want=[[1, 2, 3], [6]],
        want_paths=["$['abc']", "$['abx']"],
    ),
    Case(
        description="current key identifier, compare current array index",
        path="$.abc[?(# >= 1)]",
        data={"abc": [1, 2, 3], "def": [4, 5], "abx": [6], "aby": []},
        want=[2, 3],
        want_paths=["$['abc'][1]", "$['abc'][2]"],
    ),
    Case(
        description="object name from embedded singular query",
        path="$.a[$.b[1]]",
        data={
            "a": {"j": [1, 2, 3], "p": {"q": [4, 5, 6]}},
            "b": ["j", "p", "q"],
            "c d": {"x": {"y": 1}},
        },
        want=[{"q": [4, 5, 6]}],
        want_paths=["$['a']['p']"],
    ),
    Case(
        description="array index from embedded singular query",
        path="$.a.j[$['c d'].x.y]",
        data={
            "a": {"j": [1, 2, 3], "p": {"q": [4, 5, 6]}},
            "b": ["j", "p", "q"],
            "c d": {"x": {"y": 1}},
        },
        want=[2],
        want_paths=["$['a']['j'][1]"],
    ),
    Case(
        description="embedded singular query does not resolve to a string or int value",
        path="$.a[$.b]",
        data={
            "a": {"j": [1, 2, 3], "p": {"q": [4, 5, 6]}},
            "b": ["j", "p", "q"],
            "c d": {"x": {"y": 1}},
        },
        want=[],
        want_paths=[],
    ),
]


@pytest.fixture()
def env() -> JSONPathEnvironment:
    return JSONPathEnvironment()


@pytest.mark.parametrize("case", TEST_CASES, ids=operator.attrgetter("description"))
def test_find_extra_examples(env: JSONPathEnvironment, case: Case) -> None:
    path = env.compile(case.path)
    assert path.findall(case.data) == case.want
    assert list(path.query(case.data).locations()) == case.want_paths


@pytest.mark.parametrize("case", TEST_CASES, ids=operator.attrgetter("description"))
def test_find_extra_async(env: JSONPathEnvironment, case: Case) -> None:
    path = env.compile(case.path)

    async def coro() -> List[object]:
        return await path.findall_async(case.data)

    assert asyncio.run(coro()) == case.want
