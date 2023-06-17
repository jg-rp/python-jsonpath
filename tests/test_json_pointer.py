"""JSONPointer test cases."""
from io import StringIO
from typing import List
from typing import Union

import pytest

import jsonpath
from jsonpath import JSONPointer
from jsonpath import JSONPointerIndexError
from jsonpath import JSONPointerResolutionError


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
    parent, rv = pointer.resolve_parent(data)
    assert parent == data["some"]
    assert rv == data["some"]["thing"]


def test_resolve_with_missing_parent() -> None:
    data = {"some": {"thing": [1, 2, 3]}}
    pointer = JSONPointer("")
    parent, rv = pointer.resolve_parent(data)
    assert parent is None
    assert rv == data


def test_resolve_with_missing_target() -> None:
    data = {"some": {"thing": [1, 2, 3]}}
    pointer = JSONPointer("some/other")
    parent, rv = pointer.resolve_parent(data)
    assert parent == data
    assert rv is None


def test_resolve_from_json_string() -> None:
    data = r'{"some": {"thing": [1,2,3]}}'
    pointer = JSONPointer("/some/thing")
    assert pointer.resolve(data) == [1, 2, 3]
    assert pointer.resolve_parent(data) == ({"thing": [1, 2, 3]}, [1, 2, 3])


def test_resolve_from_file_like() -> None:
    data = StringIO(r'{"some": {"thing": [1,2,3]}}')
    pointer = JSONPointer("/some/thing")
    assert pointer.resolve(data) == [1, 2, 3]
    data.seek(0)
    assert pointer.resolve_parent(data) == ({"thing": [1, 2, 3]}, [1, 2, 3])


def test_convenience_resolve() -> None:
    data = {"some": {"thing": [1, 2, 3]}}
    assert jsonpath.resolve("/some/thing/0", data) == 1

    with pytest.raises(JSONPointerResolutionError):
        jsonpath.resolve("/some/thing/99", data)


def test_convenience_resolve_default() -> None:
    data = {"some": {"thing": [1, 2, 3]}}
    assert jsonpath.resolve("/some/thing/99", data, default=0) == 0


def test_convenience_resolve_from_parts() -> None:
    data = {"some": {"thing": [1, 2, 3]}}
    assert jsonpath.resolve(["some", "thing", "0"], data) == 1

    with pytest.raises(JSONPointerResolutionError):
        jsonpath.resolve(["some", "thing", "99"], data)


def test_convenience_resolve_default_from_parts() -> None:
    data = {"some": {"thing": [1, 2, 3]}}
    assert jsonpath.resolve(["some", "thing", "99"], data, default=0) == 0


def test_pointer_from_parts() -> None:
    parts: List[Union[str, int]] = ["some", "thing", 0]
    pointer = JSONPointer.from_parts(parts)
    assert str(pointer) == "/some/thing/0"


def test_pointer_from_uri_encoded_parts() -> None:
    parts: List[Union[str, int]] = ["some%20thing", "else", 0]
    pointer = JSONPointer.from_parts(parts, uri_decode=True)
    assert str(pointer) == "/some thing/else/0"
