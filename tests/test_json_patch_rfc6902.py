"""Test cases from rfc6902 examples.

Most of the test cases defined here are taken from rfc6902. The appropriate
Simplified BSD License is included below.

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

import copy
import dataclasses
import json
import re
from operator import attrgetter
from typing import Dict
from typing import MutableMapping
from typing import MutableSequence
from typing import Union

import pytest

from jsonpath import JSONPatch
from jsonpath.exceptions import JSONPatchError
from jsonpath.exceptions import JSONPatchTestFailure


@dataclasses.dataclass
class Case:
    description: str
    data: Union[MutableSequence[object], MutableMapping[str, object]]
    patch: JSONPatch
    op: Dict[str, object]
    want: Union[MutableSequence[object], MutableMapping[str, object]]


TEST_CASES = [
    Case(
        description="add an object member",
        data={"foo": "bar"},
        patch=JSONPatch().add(path="/baz", value="qux"),
        op={"op": "add", "path": "/baz", "value": "qux"},
        want={"foo": "bar", "baz": "qux"},
    ),
    Case(
        description="add an array element",
        data={"foo": ["bar", "baz"]},
        patch=JSONPatch().add(path="/foo/1", value="qux"),
        op={"op": "add", "path": "/foo/1", "value": "qux"},
        want={"foo": ["bar", "qux", "baz"]},
    ),
    Case(
        description="append to an array",
        data={"foo": ["bar", "baz"]},
        patch=JSONPatch().add(path="/foo/-", value="qux"),
        op={"op": "add", "path": "/foo/-", "value": "qux"},
        want={"foo": ["bar", "baz", "qux"]},
    ),
    Case(
        description="add to the root",
        data={"foo": "bar"},
        patch=JSONPatch().add(path="", value={"some": "thing"}),
        op={"op": "add", "path": "", "value": {"some": "thing"}},
        want={"some": "thing"},
    ),
    Case(
        description="remove an object member",
        data={"baz": "qux", "foo": "bar"},
        patch=JSONPatch().remove(path="/baz"),
        op={"op": "remove", "path": "/baz"},
        want={"foo": "bar"},
    ),
    Case(
        description="remove an array element",
        data={"foo": ["bar", "qux", "baz"]},
        patch=JSONPatch().remove(path="/foo/1"),
        op={"op": "remove", "path": "/foo/1"},
        want={"foo": ["bar", "baz"]},
    ),
    Case(
        description="replace an object member",
        data={"baz": "qux", "foo": "bar"},
        patch=JSONPatch().replace(path="/baz", value="boo"),
        op={"op": "replace", "path": "/baz", "value": "boo"},
        want={"baz": "boo", "foo": "bar"},
    ),
    Case(
        description="replace an array element",
        data={"foo": [1, 2, 3]},
        patch=JSONPatch().replace(path="/foo/0", value=9),
        op={"op": "replace", "path": "/foo/0", "value": 9},
        want={"foo": [9, 2, 3]},
    ),
    Case(
        description="move a value",
        data={"foo": {"bar": "baz", "waldo": "fred"}, "qux": {"corge": "grault"}},
        patch=JSONPatch().move(from_="/foo/waldo", path="/qux/thud"),
        op={"op": "move", "from": "/foo/waldo", "path": "/qux/thud"},
        want={"foo": {"bar": "baz"}, "qux": {"corge": "grault", "thud": "fred"}},
    ),
    Case(
        description="move an array element",
        data={"foo": ["all", "grass", "cows", "eat"]},
        patch=JSONPatch().move(from_="/foo/1", path="/foo/3"),
        op={"op": "move", "from": "/foo/1", "path": "/foo/3"},
        want={"foo": ["all", "cows", "eat", "grass"]},
    ),
    Case(
        description="copy a value",
        data={"foo": {"bar": "baz", "waldo": "fred"}, "qux": {"corge": "grault"}},
        patch=JSONPatch().copy(from_="/foo/waldo", path="/qux/thud"),
        op={"op": "copy", "from": "/foo/waldo", "path": "/qux/thud"},
        want={
            "foo": {"bar": "baz", "waldo": "fred"},
            "qux": {"corge": "grault", "thud": "fred"},
        },
    ),
    Case(
        description="copy an array element",
        data={"foo": ["all", "grass", "cows", "eat"]},
        patch=JSONPatch().copy(from_="/foo/1", path="/foo/3"),
        op={"op": "copy", "path": "/foo/3", "from": "/foo/1"},
        want={"foo": ["all", "grass", "cows", "grass", "eat"]},
    ),
    Case(
        description="test a value",
        data={"baz": "qux", "foo": ["a", 2, "c"]},
        patch=JSONPatch().test(path="/baz", value="qux").test(path="/foo/1", value=2),
        op={"op": "test", "path": "/baz", "value": "qux"},
        want={"baz": "qux", "foo": ["a", 2, "c"]},
    ),
    Case(
        description="add a nested member object",
        data={"foo": "bar"},
        patch=JSONPatch().add(path="/child", value={"grandchild": {}}),
        op={"op": "add", "path": "/child", "value": {"grandchild": {}}},
        want={"foo": "bar", "child": {"grandchild": {}}},
    ),
    Case(
        description="add an array value",
        data={"foo": ["bar"]},
        patch=JSONPatch().add(path="/foo/-", value=["abc", "def"]),
        op={"op": "add", "path": "/foo/-", "value": ["abc", "def"]},
        want={"foo": ["bar", ["abc", "def"]]},
    ),
]


@pytest.mark.parametrize("case", TEST_CASES, ids=attrgetter("description"))
def test_rfc6902_examples(case: Case) -> None:
    assert case.patch.apply(copy.deepcopy(case.data)) == case.want


def test_test_op_failure() -> None:
    patch = JSONPatch().test(path="/baz", value="bar")
    with pytest.raises(JSONPatchTestFailure, match=re.escape("test failed (test:0)")):
        patch.apply({"baz": "qux"})


def test_add_to_nonexistent_target() -> None:
    patch = JSONPatch().add(path="/baz/bat", value="qux")
    with pytest.raises(
        JSONPatchError, match=re.escape("pointer key error: 'baz' (add:0)")
    ):
        patch.apply({"foo": "bar"})


def test_add_array_index_out_of_range() -> None:
    patch = JSONPatch().add(path="/foo/7", value=99)
    with pytest.raises(JSONPatchError, match=re.escape("index out of range (add:0)")):
        patch.apply({"foo": [1, 2, 3]})


@pytest.mark.parametrize("case", TEST_CASES, ids=attrgetter("description"))
def test_json_patch_constructor(case: Case) -> None:
    patch = JSONPatch([case.op])
    assert len(patch.ops) == 1
    assert patch.apply(copy.deepcopy(case.data)) == case.want


@pytest.mark.parametrize(
    ("actual", "expected", "matches"),
    [
        (True, 1, False),
        (1, True, False),
        (False, 0, False),
        (0, False, False),
        (True, 1.0, False),
        (0.0, False, False),
        ([True], [1], False),
        ({"nested": False}, {"nested": 0}, False),
        ({"nested": [{"flag": True}]}, {"nested": [{"flag": 1}]}, False),
        (None, None, True),
        (True, True, True),
        (False, False, True),
        (1, 1.0, True),
        (0, -0.0, True),
        ("value", "value", True),
        ([True, 1, None], [True, 1.0, None], True),
        ({"b": [2], "a": False}, {"a": False, "b": [2.0]}, True),
        ([1, 2], [2, 1], False),
        ({"a": True}, {"b": True}, False),
        ([1], [1, 2], False),
    ],
)
@pytest.mark.parametrize("serialized", [False, True])
def test_test_op_json_equality(
    actual: object, expected: object, *, matches: bool, serialized: bool
) -> None:
    """Test uses JSON equality, including inside arrays and objects."""
    patch = (
        JSONPatch(json.dumps([{"op": "test", "path": "/value", "value": expected}]))
        if serialized
        else JSONPatch().test("/value", expected)
    )
    data = {"value": actual}
    if matches:
        assert patch.apply(data) is data
    else:
        with pytest.raises(JSONPatchTestFailure):
            patch.apply(data)


def test_test_op_deep_json_equality() -> None:
    """Nested JSON comparisons do not consume a Python frame per level."""
    actual: object = 1
    expected: object = 1.0
    for _ in range(600):
        actual = [actual]
        expected = [expected]
    data = {"value": actual}
    assert JSONPatch().test("/value", expected).apply(data) is data


def test_test_op_shared_containers() -> None:
    """Repeated references compare by their JSON contents."""
    left = {"value": [1, True]}
    right = {"value": [1.0, True]}
    data = {"value": [left, left]}
    assert JSONPatch().test("/value", [right, right]).apply(data) is data


def test_test_op_boolean_mismatch_stops_patch() -> None:
    """A failing boolean/number comparison stops later operations."""
    data = {"flag": True, "name": "original"}
    patch = JSONPatch().test("/flag", 1).replace("/name", "changed")
    with pytest.raises(JSONPatchTestFailure, match=re.escape("test failed (test:0)")):
        patch.apply(data)
    assert data == {"flag": True, "name": "original"}


def test_test_op_boolean_mismatch_is_atomic() -> None:
    """Atomic application preserves input when a later comparison fails."""
    data = {"flag": True, "name": "original"}
    patch = JSONPatch().replace("/name", "changed").test("/flag", 1)
    with pytest.raises(JSONPatchTestFailure):
        patch.atomic(data)
    assert data == {"flag": True, "name": "original"}


def test_test_op_uses_equality_for_string_subclasses() -> None:
    """The Python builder keeps equality semantics for string subclasses."""

    class StringValue(str):
        def __ne__(self, _other: object) -> bool:
            return True

    data = {"value": StringValue("same")}
    assert JSONPatch().test("/value", "same").apply(data) is data
