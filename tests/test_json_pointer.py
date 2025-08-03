"""JSONPointer test cases."""

from io import StringIO
from typing import List
from typing import Union

import pytest

import jsonpath
from jsonpath import JSONPointer
from jsonpath import JSONPointerError
from jsonpath import JSONPointerIndexError
from jsonpath import JSONPointerResolutionError
from jsonpath import JSONPointerTypeError
from jsonpath.pointer import UNDEFINED


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


def test_resolve_with_default() -> None:
    data = {"some": {"thing": "else"}}
    pointer = JSONPointer("/some/other")
    assert pointer.resolve(data, default=None) is None


def test_pointer_index_out_of_range() -> None:
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


def test_negative_index() -> None:
    data = {"some": {"thing": [1, 2, 3]}}
    pointer = JSONPointer("/some/thing/-2")
    assert pointer.resolve(data) == 2  # noqa: PLR2004


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
    pointer = JSONPointer("/some/other")
    parent, rv = pointer.resolve_parent(data)
    assert parent == data["some"]
    assert rv == UNDEFINED


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


def test_pointer_from_empty_parts() -> None:
    parts: List[Union[str, int]] = []
    pointer = JSONPointer.from_parts(parts)
    assert str(pointer) == ""


def test_pointer_from_only_empty_string_parts() -> None:
    parts: List[Union[str, int]] = [""]
    pointer = JSONPointer.from_parts(parts)
    assert str(pointer) == "/"


def test_pointer_from_uri_encoded_parts() -> None:
    parts: List[Union[str, int]] = ["some%20thing", "else", 0]
    pointer = JSONPointer.from_parts(parts, uri_decode=True)
    assert str(pointer) == "/some thing/else/0"


def test_index_with_leading_zero() -> None:
    data = {"some": {"thing": [1, 2, 3]}}
    pointer = JSONPointer("/some/thing/0")
    assert pointer.resolve(data) == 1

    pointer = JSONPointer("/some/thing/01")
    with pytest.raises(JSONPointerTypeError):
        pointer.resolve(data)

    pointer = JSONPointer("/some/thing/00")
    with pytest.raises(JSONPointerTypeError):
        pointer.resolve(data)

    pointer = JSONPointer("/some/thing/01")
    with pytest.raises(JSONPointerTypeError):
        pointer.resolve_parent(data)


def test_pointer_without_leading_slash() -> None:
    with pytest.raises(JSONPointerError):
        JSONPointer("some/thing/01")

    with pytest.raises(JSONPointerError):
        JSONPointer("nosuchthing")


def test_pointer_with_leading_whitespace() -> None:
    data = {"some": {"thing": [1, 2, 3]}}
    pointer = JSONPointer("   /some/thing/0")
    assert pointer.resolve(data) == 1
    assert str(pointer) == "/some/thing/0"


def test_pointer_parent() -> None:
    data = {"some": {"thing": [1, 2, 3]}}
    pointer = JSONPointer("/some/thing/0")
    assert pointer.resolve(data) == 1

    parent = pointer.parent()
    assert str(parent) == "/some/thing"
    assert parent.resolve(data) == [1, 2, 3]

    parent = parent.parent()
    assert str(parent) == "/some"
    assert parent.resolve(data) == {"thing": [1, 2, 3]}

    parent = parent.parent()
    assert str(parent) == ""
    assert parent.resolve(data) == {"some": {"thing": [1, 2, 3]}}

    parent = parent.parent()
    assert str(parent) == ""
    assert parent.resolve(data) == {"some": {"thing": [1, 2, 3]}}


def test_join_pointers_with_slash() -> None:
    """Test that we can join a pointer to a relative path with the `/` operator."""
    pointer = JSONPointer("/foo")
    assert str(pointer) == "/foo"
    assert str(pointer / "bar") == "/foo/bar"
    assert str(pointer / "baz") == "/foo/baz"
    assert str(pointer / "bar/baz") == "/foo/bar/baz"
    assert str(pointer / "bar/baz" / "0") == "/foo/bar/baz/0"
    assert str(pointer / "/bar") == "/bar"

    with pytest.raises(TypeError):
        pointer / 0  # type: ignore


def test_join_pointers() -> None:
    pointer = JSONPointer("/foo")
    assert str(pointer) == "/foo"
    assert str(pointer.join("bar")) == "/foo/bar"
    assert str(pointer.join("baz")) == "/foo/baz"
    assert str(pointer.join("bar/baz")) == "/foo/bar/baz"
    assert str(pointer.join("bar", "baz")) == "/foo/bar/baz"
    assert str(pointer.join("bar/baz", "0")) == "/foo/bar/baz/0"
    assert str(pointer.join("/bar")) == "/bar"
    assert str(pointer.join("/bar", "0")) == "/bar/0"

    with pytest.raises(TypeError):
        pointer.join(0)  # type: ignore


def test_pointer_exists() -> None:
    data = {"some": {"thing": [1, 2, 3]}, "other": None}
    assert JSONPointer("/some/thing").exists(data) is True
    assert JSONPointer("/other").exists(data) is True
    assert JSONPointer("/nosuchthing").exists(data) is False


def test_non_standard_property_pointer() -> None:
    data = {"foo": {"bar": [1, 2, 3], "#baz": "hello"}}
    assert JSONPointer("/foo/#bar").resolve(data) == "bar"
    assert JSONPointer("/foo/#baz").resolve(data) == "hello"


def test_non_standard_index_pointer() -> None:
    data = {"foo": {"bar": [1, 2, 3], "#baz": "hello"}}
    assert JSONPointer("/foo/bar/#1").resolve(data) == 1
    with pytest.raises(JSONPointerIndexError):
        JSONPointer("/foo/bar/#9").resolve(data)


def test_non_standard_index_pointer_with_leading_zero() -> None:
    data = {"foo": {"bar": [1, 2, 3], "#baz": "hello"}}
    with pytest.raises(JSONPointerTypeError):
        JSONPointer("/foo/bar/#01").resolve(data)

    with pytest.raises(JSONPointerTypeError):
        JSONPointer("/foo/bar/#09").resolve(data)


def test_non_standard_index_pointer_to_non_array_object() -> None:
    data = {"foo": {"bar": True, "#baz": "hello"}}
    with pytest.raises(JSONPointerTypeError):
        JSONPointer("/foo/bar/#1").resolve(data)


def test_trailing_slash() -> None:
    data = {"foo": {"": [1, 2, 3], " ": [4, 5, 6]}}
    assert JSONPointer("/foo/").resolve(data) == [1, 2, 3]
    assert JSONPointer("/foo/ ").resolve(data) == [4, 5, 6]
