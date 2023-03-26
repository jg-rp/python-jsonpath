# pylint: disable=missing-class-docstring, missing-function-docstring
# pylint: disable=missing-module-docstring
import dataclasses
import operator

import pytest

from jsonpath import JSONPathEnvironment


@dataclasses.dataclass
class Case:
    description: str
    path: str
    want: str


TEST_CASES = [
    Case(
        description="union of two paths",
        path="$.some | $.thing",
        want="$['some'] | $['thing']",
    ),
    Case(
        description="union of three paths",
        path="$.some | $.thing | [0]",
        want="$['some'] | $['thing'] | $[0]",
    ),
    # TODO: intersection
    # TODO: union and intersection on one
]


@pytest.fixture
def env() -> JSONPathEnvironment:
    return JSONPathEnvironment()


# pylint: disable=redefined-outer-name
@pytest.mark.parametrize("case", TEST_CASES, ids=operator.attrgetter("description"))
def test_parse_compound_path(env: JSONPathEnvironment, case: Case) -> None:
    path = env.compile(case.path)
    assert str(path) == case.want


# TODO: test find union and intersection
