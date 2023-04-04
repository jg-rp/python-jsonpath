"""Default filter expression comparison test cases from examples in
draft-ietf-jsonpath-base-11.

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
"""  # noqa: D205
import dataclasses
import operator

import pytest

from jsonpath import JSONPathEnvironment
from jsonpath.filter import UNDEFINED


@dataclasses.dataclass
class Case:
    description: str
    left: object
    op: str
    right: object
    want: bool


DATA = {"obj": {"x": "y"}, "arr": [2, 3]}

TEST_CASES = [
    Case(
        description="$.absent1 == $.absent2",
        left=UNDEFINED,
        op="==",
        right=UNDEFINED,
        want=True,
    ),
    Case(
        description="$.absent1 <= $.absent2",
        left=UNDEFINED,
        op="<=",
        right=UNDEFINED,
        want=True,
    ),
    Case(
        description="$.absent == 'g'",
        left=UNDEFINED,
        op="==",
        right="g",
        want=False,
    ),
    Case(
        description="$.absent1 != $.absent2",
        left=UNDEFINED,
        op="!=",
        right=UNDEFINED,
        want=False,
    ),
    Case(
        description="$.absent != 'g'",
        left=UNDEFINED,
        op="!=",
        right="g",
        want=True,
    ),
    Case(
        description="1 <= 2",
        left=1,
        op="<=",
        right=2,
        want=True,
    ),
    Case(
        description="1 > 2",
        left=1,
        op=">",
        right=2,
        want=False,
    ),
    Case(
        description="13 == '13'",
        left=13,
        op="==",
        right="13",
        want=False,
    ),
    Case(
        description="'a' <= 'b'",
        left="a",
        op="<=",
        right="b",
        want=True,
    ),
    Case(
        description="'a' > 'b'",
        left="a",
        op=">",
        right="b",
        want=False,
    ),
    Case(
        description="$.obj == $.arr",
        left=DATA["obj"],
        op="==",
        right=DATA["arr"],
        want=False,
    ),
    Case(
        description="$.obj != $.arr",
        left=DATA["obj"],
        op="!=",
        right=DATA["arr"],
        want=True,
    ),
    Case(
        description="$.obj == $.obj",
        left=DATA["obj"],
        op="==",
        right=DATA["obj"],
        want=True,
    ),
    Case(
        description="$.obj != $.obj",
        left=DATA["obj"],
        op="!=",
        right=DATA["obj"],
        want=False,
    ),
    Case(
        description="$.arr == $.arr",
        left=DATA["arr"],
        op="==",
        right=DATA["arr"],
        want=True,
    ),
    Case(
        description="$.arr != $.arr",
        left=DATA["arr"],
        op="!=",
        right=DATA["arr"],
        want=False,
    ),
    Case(
        description="$.arr == 17",
        left=DATA["arr"],
        op="==",
        right=17,
        want=False,
    ),
    Case(
        description="$.arr != 17",
        left=DATA["arr"],
        op="!=",
        right=17,
        want=True,
    ),
    Case(
        description="$.obj <= $.arr",
        left=DATA["obj"],
        op="<=",
        right=DATA["arr"],
        want=False,
    ),
    Case(
        description="$.obj < $.arr",
        left=DATA["obj"],
        op="<",
        right=DATA["arr"],
        want=False,
    ),
    Case(
        description="$.obj <= $.obj",
        left=DATA["obj"],
        op="<=",
        right=DATA["obj"],
        want=True,
    ),
    Case(
        description="$.arr <= $.arr",
        left=DATA["arr"],
        op="<=",
        right=DATA["arr"],
        want=True,
    ),
    Case(
        description="1 <= $.arr",
        left=1,
        op="<=",
        right=DATA["arr"],
        want=False,
    ),
    Case(
        description="1 >= $.arr",
        left=1,
        op=">=",
        right=DATA["arr"],
        want=False,
    ),
    Case(
        description="1 > $.arr",
        left=1,
        op=">",
        right=DATA["arr"],
        want=False,
    ),
    Case(
        description="1 < $.arr",
        left=1,
        op="<",
        right=DATA["arr"],
        want=False,
    ),
    Case(
        description="true <= true",
        left=True,
        op="<=",
        right=True,
        want=True,
    ),
    Case(
        description="true > true",
        left=True,
        op=">",
        right=True,
        want=False,
    ),
]


@pytest.fixture()
def env() -> JSONPathEnvironment:
    return JSONPathEnvironment()


@pytest.mark.parametrize("case", TEST_CASES, ids=operator.attrgetter("description"))
def test_compare_ieft(env: JSONPathEnvironment, case: Case) -> None:
    result = env.compare(case.left, case.op, case.right)
    assert result == case.want
