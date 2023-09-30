"""Function well-typedness test derived from IETF spec examples.

The test cases defined here are taken from version 11 of the JSONPath
internet draft, draft-ietf-jsonpath-base-11. In accordance with
https://trustee.ietf.org/license-info, Revised BSD License text
is included bellow.

See https://datatracker.ietf.org/doc/html/draft-ietf-jsonpath-base-20

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
from jsonpath.exceptions import JSONPathTypeError
from jsonpath.function_extensions import ExpressionType
from jsonpath.function_extensions import FilterFunction
from jsonpath.match import NodeList


@dataclasses.dataclass
class Case:
    description: str
    path: str
    valid: bool


TEST_CASES = [
    Case(
        description="length, singular query, compared",
        path="$[?length(@) < 3]",
        valid=True,
    ),
    Case(
        description="length, non-singular query, compared",
        path="$[?length(@.*) < 3]",
        valid=False,
    ),
    Case(
        description="count, non-singular query, compared",
        path="$[?count(@.*) == 1]",
        valid=True,
    ),
    Case(
        description="count, int literal, compared",
        path="$[?count(1) == 1]",
        valid=False,
    ),
    Case(
        description="nested function, LogicalType -> NodesType",
        path="$[?count(foo(@.*)) == 1]",
        valid=True,
    ),
    Case(
        description="match, singular query, string literal",
        path="$[?match(@.timezone, 'Europe/.*')]",
        valid=True,
    ),
    Case(
        description="match, singular query, string literal, compared",
        path="$[?match(@.timezone, 'Europe/.*') == true]",
        valid=False,
    ),
    Case(
        description="value, non-singular query param, comparison",
        path="$[?value(@..color) == 'red']",
        valid=True,
    ),
    Case(
        description="value, non-singular query param",
        path="$[?value(@..color)]",
        valid=False,
    ),
    Case(
        description="function, singular query, value type param, logical return type",
        path="$[?bar(@.a)]",
        valid=True,
    ),
    Case(
        description=(
            "function, non-singular query, value type param, logical return type"
        ),
        path="$[?bar(@.*)]",
        valid=False,
    ),
    Case(
        description=(
            "function, non-singular query, nodes type param, logical return type"
        ),
        path="$[?bn(@.*)]",
        valid=True,
    ),
    Case(
        description=(
            "function, non-singular query, logical type param, logical return type"
        ),
        path="$[?bl(@.*)]",
        valid=True,
    ),
    Case(
        description="function, logical type param, comparison, logical return type",
        path="$[?bl(1==1)]",
        valid=True,
    ),
    Case(
        description="function, logical type param, literal, logical return type",
        path="$[?bl(1)]",
        valid=False,
    ),
    Case(
        description="function, value type param, literal, logical return type",
        path="$[?bar(1)]",
        valid=True,
    ),
]


class MockFoo(FilterFunction):
    arg_types = [ExpressionType.NODES]
    return_type = ExpressionType.NODES

    def __call__(self, nodes: NodeList) -> NodeList:  # noqa: D102
        return nodes


class MockBar(FilterFunction):
    arg_types = [ExpressionType.VALUE]
    return_type = ExpressionType.LOGICAL

    def __call__(self) -> bool:  # noqa: D102
        return False


class MockBn(FilterFunction):
    arg_types = [ExpressionType.NODES]
    return_type = ExpressionType.LOGICAL

    def __call__(self, _: object) -> bool:  # noqa: D102
        return False


class MockBl(FilterFunction):
    arg_types = [ExpressionType.LOGICAL]
    return_type = ExpressionType.LOGICAL

    def __call__(self, _: object) -> bool:  # noqa: D102
        return False


@pytest.fixture()
def env() -> JSONPathEnvironment:
    environment = JSONPathEnvironment()
    environment.function_extensions["foo"] = MockFoo()
    environment.function_extensions["bar"] = MockBar()
    environment.function_extensions["bn"] = MockBn()
    environment.function_extensions["bl"] = MockBl()
    return environment


@pytest.mark.parametrize("case", TEST_CASES, ids=operator.attrgetter("description"))
def test_ietf_well_typedness(env: JSONPathEnvironment, case: Case) -> None:
    if case.valid:
        env.compile(case.path)
    else:
        with pytest.raises(JSONPathTypeError):
            env.compile(case.path)
