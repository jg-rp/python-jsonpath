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
    Case(
        description="intersection of two paths",
        path="$.some.* & $.thing.*",
        want="$['some'][*] & $['thing'][*]",
    ),
    Case(
        description="intersection then union",
        path="$.some.* & $.thing.* | $.other",
        want="$['some'][*] & $['thing'][*] | $['other']",
    ),
]


@pytest.fixture()
def env() -> JSONPathEnvironment:
    return JSONPathEnvironment()


@pytest.mark.parametrize("case", TEST_CASES, ids=operator.attrgetter("description"))
def test_parse_compound_path(env: JSONPathEnvironment, case: Case) -> None:
    path = env.compile(case.path)
    assert str(path) == case.want
