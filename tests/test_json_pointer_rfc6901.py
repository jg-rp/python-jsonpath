"""Test cases from rfc6901 examples.

The test cases defined here are taken from rfc6901. The appropriate Simplified
BSD License is included below.

Copyright (c) 2013 IETF Trust and the persons identified as authors of the
code. All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

- Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.
- Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.
- Neither the name of Internet Society, IETF or IETF Trust, nor the names of
  specific contributors, may be used to endorse or promote products derived
  from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS “AS IS”
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
"""
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
