import dataclasses
import operator
from typing import Any
from typing import Mapping
from typing import Sequence
from typing import Union

import pytest

from jsonpath import JSONPathEnvironment
from jsonpath import function_extensions


@dataclasses.dataclass
class Case:
    description: str
    path: str
    data: Union[Sequence[Any], Mapping[str, Any]]
    want: Union[Sequence[Any], Mapping[str, Any]]


TEST_CASES = [
    Case(
        description="value in keys of an object",
        path="$.some[?'thing' in keys(@)]",
        data={"some": [{"thing": "foo"}]},
        want=[{"thing": "foo"}],
    ),
    Case(
        description="value not in keys of an object",
        path="$.some[?'else' in keys(@)]",
        data={"some": [{"thing": "foo"}]},
        want=[],
    ),
    Case(
        description="keys of an array",
        path="$[?'thing' in keys(@)]",
        data={"some": [{"thing": "foo"}]},
        want=[],
    ),
    Case(
        description="keys of an string value",
        path="$some[0].thing[?'else' in keys(@)]",
        data={"some": [{"thing": "foo"}]},
        want=[],
    ),
]


@pytest.fixture()
def env() -> JSONPathEnvironment:
    _env = JSONPathEnvironment()
    _env.function_extensions["keys"] = function_extensions.Keys()
    return _env


@pytest.mark.parametrize("case", TEST_CASES, ids=operator.attrgetter("description"))
def test_isinstance_function(env: JSONPathEnvironment, case: Case) -> None:
    path = env.compile(case.path)
    assert path.findall(case.data) == case.want
