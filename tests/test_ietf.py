"""Test cases from examples in draft-ietf-jsonpath-base-11.

The test cases defined here are taken from version 11 of the JSONPath
internet draft, draft-ietf-jsonpath-base-11. In accordance with
https://trustee.ietf.org/license-info, Revised BSD License text
is included bellow.

See https://datatracker.ietf.org/doc/html/draft-ietf-jsonpath-base-11

Copyright (c) 2023 IETF Trust and the persons identified as authors
of the code. All rights reserved.Redistribution and use in source and
binary forms, with or without modification, are permitted provided
that the following conditions are met:

- Redistributions of source code must retain the above copyright
  notice, this list of conditions and the following disclaimer.
- Redistributions in binary form must reproduce the above copyright
  notice, this list of conditions and the following disclaimer in the
  documentation and/or other materials provided with the
  distribution.
- Neither the name of Internet Society, IETF or IETF Trust, nor the
  names of specific contributors, may be used to endorse or promote
  products derived from this software without specific prior written
  permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
“AS IS” AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
# pylint: disable=missing-class-docstring, missing-function-docstring

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
    Case(description="root", path="$", data={"k": "v"}, want=[{"k": "v"}]),
    Case(
        description="name selector - named value in nested object (single quote)",
        path="$.o['j j']['k.k']",
        data={"o": {"j j": {"k.k": 3}}, "'": {"@": 2}},
        want=[3],
    ),
    Case(
        description="name selector - named value in nested object (double quote)",
        path='$.o["j j"]["k.k"]',
        data={"o": {"j j": {"k.k": 3}}, "'": {"@": 2}},
        want=[3],
    ),
    Case(
        description="name selector - unusual member names",
        path='$["\'"]["@"]',
        data={"o": {"j j": {"k.k": 3}}, "'": {"@": 2}},
        want=[2],
    ),
    Case(
        description="wildcard selector - object values",
        path="$[*]",
        data={"o": {"j": 1, "k": 2}, "a": [5, 3]},
        want=[{"j": 1, "k": 2}, [5, 3]],
    ),
    Case(
        description="wildcard selector - object values (dot property)",
        path="$.o[*]",
        data={"o": {"j": 1, "k": 2}, "a": [5, 3]},
        want=[1, 2],
    ),
    # Case(
    #     description="wildcard selector - double wild",
    #     path="$.o[*, *]",
    #     data={"o": {"j": 1, "k": 2}, "a": [5, 3]},
    #     want=[1, 2, 1, 2],
    # ),
    Case(
        description="wildcard selector - dot property wild",
        path="$.a[*]",
        data={"o": {"j": 1, "k": 2}, "a": [5, 3]},
        want=[5, 3],
    ),
    Case(
        description="index selector - element of array",
        path="$[1]",
        data=["a", "b"],
        want=["b"],
    ),
    Case(
        description="index selector - element of array, from the end",
        path="$[-2]",
        data=["a", "b"],
        want=["a"],
    ),
    Case(
        description="array slice selector - slice with default step",
        path="$[1:3]",
        data=["a", "b", "c", "d", "e", "f", "g"],
        want=["b", "c"],
    ),
    Case(
        description="array slice selector - slice with negative step",
        path="$[5:1:-2]",
        data=["a", "b", "c", "d", "e", "f", "g"],
        want=["f", "d"],
    ),
    Case(
        description="array slice selector - slice in reverse order",
        path="$[::-1]",
        data=["a", "b", "c", "d", "e", "f", "g"],
        want=["g", "f", "e", "d", "c", "b", "a"],
    ),
    # TODO: Filter selector examples
    # TODO: child segment examples
]


@pytest.fixture
def env() -> JSONPathEnvironment:
    return JSONPathEnvironment()


# pylint: disable=redefined-outer-name
@pytest.mark.parametrize("case", TEST_CASES, ids=operator.attrgetter("description"))
def test_find_ieft(env: JSONPathEnvironment, case: Case) -> None:
    path = env.compile(case.path)
    assert path.findall(case.data) == case.want


@pytest.mark.parametrize("case", TEST_CASES, ids=operator.attrgetter("description"))
def test_find_ieft_async(env: JSONPathEnvironment, case: Case) -> None:
    path = env.compile(case.path)

    async def coro() -> List[object]:
        return await path.findall_async(case.data)

    assert asyncio.run(coro()) == case.want
