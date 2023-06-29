"""JSON Patch test cases."""

import json
import re
from collections.abc import Mapping
from io import StringIO
from typing import Any
from typing import Iterator

import pytest

from jsonpath import JSONPatch
from jsonpath import patch
from jsonpath.exceptions import JSONPatchError


class MockMapping(Mapping):  # type: ignore
    def __getitem__(self, __key: Any) -> Any:
        return "foo"

    def __iter__(self) -> Iterator[str]:
        return iter(["foo"])

    def __len__(self) -> int:
        return 1


def test_add_to_immutable_mapping() -> None:
    patch = JSONPatch().add("/foo/bar", "baz")
    with pytest.raises(
        JSONPatchError, match=re.escape("unexpected operation on 'MockMapping' (add:0)")
    ):
        patch.apply({"foo": MockMapping()})


def test_remove_root() -> None:
    patch = JSONPatch().remove("")
    with pytest.raises(JSONPatchError, match=re.escape("can't remove root (remove:0)")):
        patch.apply({"foo": "bar"})


def test_remove_nonexistent_value() -> None:
    patch = JSONPatch().remove("/baz")
    with pytest.raises(
        JSONPatchError, match=re.escape("can't remove nonexistent property (remove:0)")
    ):
        patch.apply({"foo": "bar"})


def test_remove_array_end() -> None:
    patch = JSONPatch().remove("/foo/-")
    with pytest.raises(
        JSONPatchError, match=re.escape("can't remove nonexistent item (remove:0)")
    ):
        patch.apply({"foo": [1, 2, 3]})


def test_remove_from_immutable_mapping() -> None:
    patch = JSONPatch().remove("/bar/foo")
    with pytest.raises(
        JSONPatchError,
        match=re.escape("unexpected operation on 'MockMapping' (remove:0)"),
    ):
        patch.apply({"bar": MockMapping()})


def test_replace_root() -> None:
    assert patch.apply(
        [{"op": "replace", "path": "", "value": [1, 2, 3]}], {"foo": "bar"}
    ) == [1, 2, 3]


def test_replace_a_nonexistent_item() -> None:
    with pytest.raises(
        JSONPatchError, match=re.escape("can't replace nonexistent item (replace:0)")
    ):
        patch.apply(
            [{"op": "replace", "path": "/foo/99", "value": 5}], {"foo": [1, 2, 3]}
        )


def test_replace_a_nonexistent_value() -> None:
    with pytest.raises(
        JSONPatchError,
        match=re.escape("can't replace nonexistent property (replace:0)"),
    ):
        patch.apply(
            [{"op": "replace", "path": "/foo/bar", "value": 5}], {"foo": {"baz": 10}}
        )


def test_replace_immutable_mapping() -> None:
    with pytest.raises(
        JSONPatchError,
        match=re.escape("unexpected operation on 'MockMapping' (replace:0)"),
    ):
        patch.apply(
            [{"op": "replace", "path": "/bar/foo", "value": "baz"}],
            {"bar": MockMapping()},
        )


def test_move_to_child() -> None:
    with pytest.raises(
        JSONPatchError,
        match=re.escape("can't move object to one of its own children (move:0)"),
    ):
        patch.apply(
            [{"op": "move", "from": "/foo/bar", "path": "/foo/bar/baz"}],
            {"foo": {"bar": {"baz": [1, 2, 3]}}},
        )


def test_move_nonexistent_value() -> None:
    with pytest.raises(
        JSONPatchError, match=re.escape("source object does not exist (move:0)")
    ):
        JSONPatch().move(from_="/foo/bar", path="/bar").apply({"foo": {"baz": 1}})


def test_move_to_root() -> None:
    patch = JSONPatch().move(from_="/foo", path="")
    assert patch.apply({"foo": {"bar": "baz"}}) == {"bar": "baz"}


def test_move_to_immutable_mapping() -> None:
    patch = JSONPatch().move(from_="/foo/bar", path="/baz/bar")
    with pytest.raises(
        JSONPatchError,
        match=re.escape("unexpected operation on 'MockMapping' (move:0)"),
    ):
        patch.apply({"foo": {"bar": "hello"}, "baz": MockMapping()})


def test_copy_nonexistent_value() -> None:
    with pytest.raises(
        JSONPatchError, match=re.escape("source object does not exist (copy:0)")
    ):
        JSONPatch().copy(from_="/foo/bar", path="/bar").apply({"foo": {"baz": "hello"}})


def test_copy_to_root() -> None:
    patch = JSONPatch().copy(from_="/foo/bar", path="")
    assert patch.apply({"foo": {"bar": [1, 2, 3]}}) == [1, 2, 3]


def test_copy_to_immutable_mapping() -> None:
    with pytest.raises(
        JSONPatchError,
        match=re.escape("unexpected operation on 'MockMapping' (copy:0)"),
    ):
        JSONPatch().copy(from_="/foo/bar", path="/baz/bar").apply(
            {"foo": {"bar": [1, 2, 3]}, "baz": MockMapping()}
        )


def test_patch_from_file_like() -> None:
    patch_doc = StringIO(
        json.dumps(
            [
                {"op": "add", "path": "", "value": {"foo": {}}},
                {"op": "add", "path": "/foo", "value": {"bar": []}},
                {"op": "add", "path": "/foo/bar/-", "value": 1},
            ]
        )
    )

    patch = JSONPatch(patch_doc)
    assert patch.apply({}) == {"foo": {"bar": [1]}}


def test_patch_from_string() -> None:
    patch_doc = json.dumps(
        [
            {"op": "add", "path": "", "value": {"foo": {}}},
            {"op": "add", "path": "/foo", "value": {"bar": []}},
            {"op": "add", "path": "/foo/bar/-", "value": 1},
        ]
    )

    patch = JSONPatch(patch_doc)
    assert patch.apply({}) == {"foo": {"bar": [1]}}


def test_unexpected_patch_ops() -> None:
    with pytest.raises(
        JSONPatchError,
        match=re.escape("expected a sequence of patch operations, found 'MockMapping'"),
    ):
        JSONPatch(MockMapping())  # type: ignore


def test_construct_missing_op() -> None:
    with pytest.raises(JSONPatchError, match=re.escape("missing 'op' member at op 0")):
        JSONPatch([{}])


def test_construct_unknown_op() -> None:
    msg = (
        "expected 'op' to be one of 'add', 'remove', 'replace', "
        "'move', 'copy' or 'test' (foo:0)"
    )
    with pytest.raises(JSONPatchError, match=re.escape(msg)):
        JSONPatch([{"op": "foo"}])


def test_construct_missing_pointer() -> None:
    msg = "missing property 'path' (add:0)"
    with pytest.raises(JSONPatchError, match=re.escape(msg)):
        JSONPatch([{"op": "add", "value": "foo"}])


def test_construct_missing_value() -> None:
    msg = "missing property 'value' (add:0)"
    with pytest.raises(JSONPatchError, match=re.escape(msg)):
        JSONPatch([{"op": "add", "path": "/foo"}])


def test_construct_pointer_not_a_string() -> None:
    msg = "expected a JSON Pointer string for 'path', found 'int' (add:0)"
    with pytest.raises(JSONPatchError, match=re.escape(msg)):
        JSONPatch([{"op": "add", "path": 5, "value": "foo"}])


def test_apply_to_str() -> None:
    patch_doc = json.dumps(
        [
            {"op": "add", "path": "", "value": {"foo": {}}},
            {"op": "add", "path": "/foo", "value": {"bar": []}},
            {"op": "add", "path": "/foo/bar/-", "value": 1},
        ]
    )

    data_doc = json.dumps({})
    assert patch.apply(patch_doc, data_doc) == {"foo": {"bar": [1]}}


def test_apply_to_file_like() -> None:
    patch_doc = StringIO(
        json.dumps(
            [
                {"op": "add", "path": "", "value": {"foo": {}}},
                {"op": "add", "path": "/foo", "value": {"bar": []}},
                {"op": "add", "path": "/foo/bar/-", "value": 1},
            ]
        )
    )

    data_doc = StringIO(json.dumps({}))
    assert patch.apply(patch_doc, data_doc) == {"foo": {"bar": [1]}}
