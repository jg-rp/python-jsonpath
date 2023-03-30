"""Default filter expression comparison test cases."""
import dataclasses
import operator

import pytest

from jsonpath import JSONPathEnvironment


@dataclasses.dataclass
class Case:
    description: str
    left: object
    op: str
    right: object
    want: bool


TEST_CASES = [
    Case(
        description="true and true",
        left=True,
        op="&&",
        right=True,
        want=True,
    ),
    Case(
        description="left in right",
        left="thing",
        op="in",
        right=["some", "thing"],
        want=True,
    ),
    Case(
        description="right contains left",
        left=["some", "thing"],
        op="contains",
        right="thing",
        want=True,
    ),
    Case(
        description="string >= string",
        left="thing",
        op=">=",
        right="thing",
        want=True,
    ),
    Case(
        description="string < string",
        left="abc",
        op="<",
        right="bcd",
        want=True,
    ),
    Case(
        description="string > string",
        left="bcd",
        op=">",
        right="abcd",
        want=True,
    ),
    Case(
        description="int >= int",
        left=2,
        op=">=",
        right=1,
        want=True,
    ),
    Case(
        description="nil >= nil",
        left=None,
        op=">=",
        right=None,
        want=True,
    ),
    Case(
        description="nil <= nil",
        left=None,
        op="<=",
        right=None,
        want=True,
    ),
]


@pytest.fixture()
def env() -> JSONPathEnvironment:
    return JSONPathEnvironment()


@pytest.mark.parametrize("case", TEST_CASES, ids=operator.attrgetter("description"))
def test_compare(env: JSONPathEnvironment, case: Case) -> None:
    result = env.compare(case.left, case.op, case.right)
    assert result == case.want
