"""JSONPointer test cases."""
import dataclasses

import pytest

from jsonpath import JSONPointer


@dataclasses.dataclass
class Case:
    pointer: str
    want: object


RFC6901_DOCUMENT = {
    "foo": ["bar", "baz"],
    "": 0,
    "a/b": 1,
    "c%d": 2,
    "e^f": 3,
    "g|h": 4,
    "i\\j": 5,
    'k"l': 6,
    " ": 7,
    "m~n": 8,
}

RFC6901_TEST_CASES = [
    Case(pointer="", want=RFC6901_DOCUMENT),
    Case(pointer="/foo", want=["bar", "baz"]),
    Case(pointer="/foo/0", want="bar"),
    Case(pointer="/", want=0),
    Case(pointer="/a~1b", want=1),
    Case(pointer="/c%d", want=2),
    Case(pointer="/e^f", want=3),
    Case(pointer="/g|h", want=4),
    Case(pointer=r"/i\\j", want=5),
    Case(pointer='/k"l', want=6),
    Case(pointer="/ ", want=7),
    Case(pointer="/m~0n", want=8),
]

RFC6901_URI_TEST_CASES = [
    Case("", want=RFC6901_DOCUMENT),
    Case("/foo", want=["bar", "baz"]),
    Case("/foo/0", want="bar"),
    Case("/", want=0),
    Case("/a~1b", want=1),
    Case("/c%25d", want=2),
    Case("/e%5Ef", want=3),
    Case("/g%7Ch", want=4),
    Case("/i%5Cj", want=5),
    Case("/k%22l", want=6),
    Case("/%20", want=7),
    Case("/m~0n", want=8),
]


@pytest.mark.parametrize("case", RFC6901_TEST_CASES)
def test_rfc6901_examples(case: Case) -> None:
    pointer = JSONPointer(case.pointer)
    assert pointer.resolve(RFC6901_DOCUMENT) == case.want


@pytest.mark.parametrize("case", RFC6901_URI_TEST_CASES)
def test_rfc6901_uri_examples(case: Case) -> None:
    pointer = JSONPointer(case.pointer, unicode_escape=False, uri_decode=True)
    assert pointer.resolve(RFC6901_DOCUMENT) == case.want
