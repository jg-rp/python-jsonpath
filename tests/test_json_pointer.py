"""JSONPointer test cases."""
import pytest

import jsonpath
from jsonpath import JSONPointer
from jsonpath import JSONPointerIndexError


def test_match_to_pointer() -> None:
    data = {"some": {"thing": "else"}}
    matches = list(jsonpath.finditer("$.some.thing", data))
    assert len(matches) == 1
    match = matches[0]
    pointer = match.pointer()
    assert pointer.resolve(data) == match.obj
    assert pointer.resolve({"some": {"thing": "foo"}}) == "foo"


def test_pointer_repr() -> None:
    data = {"some": {"thing": "else"}}
    matches = list(jsonpath.finditer("$.some.thing", data))
    assert len(matches) == 1
    match = matches[0]
    pointer = match.pointer()
    assert str(pointer) == "/some/thing"


def test_pointer_index_out_fo_range() -> None:
    max_plus_one = JSONPointer.max_int_index + 1
    min_minus_one = JSONPointer.min_int_index - 1

    with pytest.raises(jsonpath.JSONPointerError):
        JSONPointer(f"/some/thing/{max_plus_one}")

    with pytest.raises(jsonpath.JSONPointerError):
        JSONPointer(f"/some/thing/{min_minus_one}")


def test_resolve_int_key() -> None:
    data = {"some": {"1": "thing"}}
    pointer = JSONPointer("/some/1")
    assert pointer.resolve(data) == "thing"


def test_resolve_int_missing_key() -> None:
    data = {"some": {"1": "thing"}}
    pointer = JSONPointer("/some/2")
    with pytest.raises(KeyError):
        pointer.resolve(data)


def test_resolve_str_index() -> None:
    data = {"some": ["a", "b", "c"]}
    pointer = JSONPointer("/some/1", parts=("some", "1"))
    assert pointer.resolve(data) == "b"


def test_keys_selector() -> None:
    data = {"some": {"thing": "else"}}
    matches = list(jsonpath.finditer("$.some.~", data))
    assert len(matches) == 1
    match = matches[0]
    pointer = match.pointer()
    assert str(pointer) == "/some/~0thing"
    assert pointer.resolve(data) == "thing"


def test_mapping_key_error() -> None:
    data = {"some": {"thing": "else"}}
    pointer = JSONPointer("/some/other")
    with pytest.raises(KeyError):
        pointer.resolve(data)


def test_sequence_type_error() -> None:
    data = {"some": ["a", "b", "c"]}
    pointer = JSONPointer("/some/thing")
    with pytest.raises(TypeError):
        pointer.resolve(data)


def test_hyphen_index() -> None:
    data = {"some": {"thing": [1, 2, 3]}}
    pointer = JSONPointer("/some/thing/-")
    with pytest.raises(JSONPointerIndexError):
        pointer.resolve(data)


def test_resolve_with_parent() -> None:
    data = {"some": {"thing": [1, 2, 3]}}
    pointer = JSONPointer("/some/thing")
    parent, rv = pointer.resolve_with_parent(data)
    assert parent == data["some"]
    assert rv == data["some"]["thing"]


def test_resolve_with_missing_parent() -> None:
    data = {"some": {"thing": [1, 2, 3]}}
    pointer = JSONPointer("")
    parent, rv = pointer.resolve_with_parent(data)
    assert parent is None
    assert rv == data
