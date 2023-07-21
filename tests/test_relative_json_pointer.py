"""Relative JSON Pointer test cases."""
import pytest

from jsonpath import JSONPointer
from jsonpath import RelativeJSONPointer
from jsonpath import RelativeJSONPointerIndexError
from jsonpath import RelativeJSONPointerSyntaxError


def test_syntax_error() -> None:
    with pytest.raises(RelativeJSONPointerSyntaxError):
        RelativeJSONPointer("foo")


def test_origin_leading_zero() -> None:
    with pytest.raises(RelativeJSONPointerSyntaxError):
        RelativeJSONPointer("01")


def test_origin_beyond_pointer() -> None:
    pointer = JSONPointer("/foo/bar/0")
    rel = RelativeJSONPointer("9/foo")
    with pytest.raises(RelativeJSONPointerIndexError):
        rel.to(pointer)


def test_equality() -> None:
    rel = RelativeJSONPointer("1/foo")
    assert rel == RelativeJSONPointer("1/foo")


def test_zero_index_offset() -> None:
    with pytest.raises(RelativeJSONPointerSyntaxError):
        RelativeJSONPointer("1-0")

    with pytest.raises(RelativeJSONPointerSyntaxError):
        RelativeJSONPointer("1+0")


def test_negative_index_offset() -> None:
    pointer = JSONPointer("/foo/1")
    rel = RelativeJSONPointer("0-2")
    with pytest.raises(RelativeJSONPointerIndexError):
        rel.to(pointer)
