import dataclasses
import operator
from typing import Any
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
        description="current value start with string",
        path="$[?startswith(@, 'ab')]",
        data={"x": "abc", "y": "abx", "z": "bcd", "-": "ab"},
        want=["abc", "abx", "ab"],
    ),
    Case(
        description="current key start with string",
        path="$[?startswith(#, 'ab')]",
        data={"abc": 1, "abx": 2, "bcd": 3, "ab": 4},
        want=[1, 2, 4],
    ),
    Case(
        description="value is not a string",
        path="$[?startswith(@, 'ab')]",
        data={"abc": 1, "abx": 2, "bcd": 3, "ab": 4},
        want=[],
    ),
]


@pytest.fixture()
def env() -> JSONPathEnvironment:
    return JSONPathEnvironment()


@pytest.mark.parametrize("case", TEST_CASES, ids=operator.attrgetter("description"))
def test_isinstance_function(env: JSONPathEnvironment, case: Case) -> None:
    path = env.compile(case.path)
    assert path.findall(case.data) == case.want
