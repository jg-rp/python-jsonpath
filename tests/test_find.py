# pylint: disable=missing-class-docstring, missing-function-docstring
import dataclasses
import operator

from typing import Any
from typing import Mapping
from typing import Sequence
from typing import Union

import pytest

from python_jsonpath import JSONPathEnvironment


@dataclasses.dataclass
class Case:
    description: str
    path: str
    data: Union[Sequence[Any], Mapping[str, Any]]
    want: Union[Sequence[Any], Mapping[str, Any]]


# From the original article by Stefan Gössner.
# See https://goessner.net/articles/JsonPath/
DATA = {
    "store": {
        "book": [
            {
                "category": "reference",
                "author": "Nigel Rees",
                "title": "Sayings of the Century",
                "price": 8.95,
            },
            {
                "category": "fiction",
                "author": "Evelyn Waugh",
                "title": "Sword of Honour",
                "price": 12.99,
            },
            {
                "category": "fiction",
                "author": "Herman Melville",
                "title": "Moby Dick",
                "isbn": "0-553-21311-3",
                "price": 8.99,
            },
            {
                "category": "fiction",
                "author": "J. R. R. Tolkien",
                "title": "The Lord of the Rings",
                "isbn": "0-395-19395-8",
                "price": 22.99,
            },
        ],
        "bicycle": {"color": "red", "price": 19.95},
    }
}

TEST_CASES = [
    Case(
        description="(reference) all authors",
        path="$..author",
        data=DATA,
        want=["Nigel Rees", "Evelyn Waugh", "Herman Melville", "J. R. R. Tolkien"],
    ),
]


@pytest.fixture
def env() -> JSONPathEnvironment:
    return JSONPathEnvironment()


# pylint: disable=redefined-outer-name
@pytest.mark.parametrize("case", TEST_CASES, ids=operator.attrgetter("description"))
def test_find(env: JSONPathEnvironment, case: Case) -> None:
    path = env.compile(case.path)
    assert path.findall(case.data) == case.want
