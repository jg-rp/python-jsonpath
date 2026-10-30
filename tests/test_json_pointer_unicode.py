"""Native Unicode pointers and JSON Patch targets retain their characters."""

from __future__ import annotations

import json
from typing import Dict
from typing import List
from urllib.parse import quote

import pytest

from jsonpath import JSONPatch
from jsonpath import JSONPointer
from jsonpath import finditer
from jsonpath import patch
from jsonpath import pointer

_VALUE = 7
_OTHER_VALUE = 9

KEYS = [
    "café",
    "漢字",
    "😀",
    "e\N{COMBINING ACUTE ACCENT}",
    "café/part~name",
    "café%2F",
    'café"quoted',
    "café\n\t\0",
    "café\\😀",
    "café\\\\😀",
]


def _token(key: str) -> str:
    return key.replace("~", "~0").replace("/", "~1")


@pytest.mark.parametrize("key", KEYS)
def test_native_unicode_pointer(key: str) -> None:
    # A raw pointer has already been decoded by its transport. Backslashes
    # are literal when compatibility escape decoding is disabled.
    data = {key: _VALUE}
    value = JSONPointer("/" + _token(key), unicode_escape=False)
    assert value.resolve(data) == _VALUE
    assert str(value) == "/" + _token(key)


@pytest.mark.parametrize("key", KEYS)
def test_unicode_with_compatibility_escapes(key: str) -> None:
    # JSON's encoder provides the escape spelling; this is not another
    # implementation of the pointer's decoder. Native Unicode stays literal.
    encoded = json.dumps(_token(key), ensure_ascii=False)[1:-1]
    value = JSONPointer("/" + encoded, unicode_escape=True)
    assert value.resolve({key: _VALUE}) == _VALUE
    assert str(value) == "/" + _token(key)


@pytest.mark.parametrize("key", ["café", "漢字", "😀", "e\N{COMBINING ACUTE ACCENT}"])
def test_default_pointer_and_convenience_api(key: str) -> None:
    data = {key: _VALUE}
    assert JSONPointer("/" + key).resolve(data) == _VALUE
    assert pointer.resolve("/" + key, data) == _VALUE
    assert JSONPointer.from_parts([key]).resolve(data) == _VALUE
    assert (JSONPointer("") / key).resolve(data) == _VALUE
    assert JSONPointer("").join(key).resolve(data) == _VALUE


@pytest.mark.parametrize("unicode_escape", [False, True])
@pytest.mark.parametrize("key", KEYS)
def test_uri_decoding_preserves_native_unicode(
    key: str, *, unicode_escape: bool
) -> None:
    encoded = _token(key)
    if unicode_escape:
        encoded = json.dumps(encoded, ensure_ascii=False)[1:-1]
    value = JSONPointer(
        quote("/" + encoded, safe="/~"),
        unicode_escape=unicode_escape,
        uri_decode=True,
    )
    assert value.resolve({key: _VALUE}) == _VALUE


def test_unicode_normalization_is_not_applied() -> None:
    data = {"é": 1, "e\N{COMBINING ACUTE ACCENT}": 2}
    assert JSONPointer("/é").resolve(data) == 1
    assert (
        JSONPointer("/e\N{COMBINING ACUTE ACCENT}").resolve(data)
        == data["e\N{COMBINING ACUTE ACCENT}"]
    )


def test_escaped_unicode_and_native_unicode_can_be_mixed() -> None:
    value = JSONPointer("/café/" + r"\ud83d\ude00")
    assert value.resolve({"café": {"😀": _VALUE}}) == _VALUE
    assert str(value) == "/café/😀"


def test_unicode_escape_flag_preserves_literal_escape_spelling() -> None:
    data = {r"café\u0061": _VALUE, "caféa": _OTHER_VALUE}
    assert JSONPointer(r"/café\u0061", unicode_escape=False).resolve(data) == _VALUE
    assert (
        JSONPointer(r"/café\u0061", unicode_escape=True).resolve(data) == _OTHER_VALUE
    )


def test_percent_decoding_is_separate_from_unicode_escapes() -> None:
    data = {"café%2F": _VALUE, "café%252F": _OTHER_VALUE}
    assert JSONPointer("/café%252F", uri_decode=True).resolve(data) == _VALUE
    assert JSONPointer("/café%252F", uri_decode=False).resolve(data) == _OTHER_VALUE


def test_a_pointer_from_a_query_match_keeps_its_native_parts() -> None:
    data = {"café": {"😀": _VALUE}}
    match = next(iter(finditer("$['café']['😀']", data)))
    assert match.pointer().resolve(data) == _VALUE
    assert str(match.pointer()) == "/café/😀"


@pytest.mark.parametrize(
    "operation", ["add", "replace", "remove", "copy", "move", "test"]
)
@pytest.mark.parametrize("encoding", ["objects", "unicode-json", "ascii-json"])
@pytest.mark.parametrize("unicode_escape", [False, True])
def test_patch_targets_the_native_key(
    operation: str, encoding: str, *, unicode_escape: bool
) -> None:
    # Both keys exist so a lossy decoder silently changes the wrong member
    # instead of raising. JSON input is decoded before pointer processing.
    data = {"café": {"value": 1}, "cafÃ©": {"value": _OTHER_VALUE}}
    operations: List[Dict[str, object]]
    if operation in ("copy", "move"):
        operations = [{"op": operation, "from": "/café", "path": "/target"}]
    elif operation == "test":
        operations = [{"op": operation, "path": "/café/value", "value": 1}]
    elif operation == "remove":
        operations = [{"op": operation, "path": "/café"}]
    else:
        operations = [{"op": operation, "path": "/café/value", "value": 2}]

    value = (
        operations
        if encoding == "objects"
        else json.dumps(operations, ensure_ascii=encoding == "ascii-json")
    )
    result = patch.apply(value, data, unicode_escape=unicode_escape)
    assert result is data
    assert data["cafÃ©"] == {"value": _OTHER_VALUE}
    if operation in ("remove", "move"):
        assert "café" not in data
    else:
        assert data["café"] == {"value": 1 if operation in ("copy", "test") else 2}
    if operation in ("copy", "move"):
        assert data["target"] == {"value": 1}


def test_patched_and_atomic_operations_preserve_native_targets() -> None:
    source = {"café": [1], "cafÃ©": [_OTHER_VALUE]}
    operations = JSONPatch().replace("/café/0", 2)
    assert operations.patched(source) == {"café": [2], "cafÃ©": [_OTHER_VALUE]}
    assert source == {"café": [1], "cafÃ©": [_OTHER_VALUE]}
    assert operations.atomic(source) is source
    assert source == {"café": [2], "cafÃ©": [_OTHER_VALUE]}


@pytest.mark.parametrize(
    "suffix",
    [r"\u12", r"\xZZ", r"\U00110000", r"\N{NO SUCH NAME}", r"\ud800", "\\"],
)
def test_malformed_compatibility_escapes_are_still_refused(suffix: str) -> None:
    with pytest.raises(UnicodeDecodeError):
        JSONPointer("/café/" + suffix)


@pytest.mark.parametrize("key", [r"café\😀", r"café\é", r"漢\字"])
def test_backslash_before_native_unicode_is_literal(key: str) -> None:
    assert JSONPointer("/" + key).resolve({key: _VALUE}) == _VALUE


@pytest.mark.parametrize(
    ("encoded", "key"),
    [
        (r"\x61", "a"),
        (r"\141", "a"),
        (r"\U0001f600", "😀"),
        (r"\N{GRINNING FACE}", "😀"),
        (r"\ud83d\ude00", "😀"),
        (r"\\u0061", r"\u0061"),
    ],
)
def test_compatibility_escapes_with_a_native_prefix(encoded: str, key: str) -> None:
    assert JSONPointer("/café/" + encoded).resolve({"café": {key: _VALUE}}) == _VALUE


@pytest.mark.parametrize("units", [chr(0xD800), chr(0xDC00), chr(0xD800) + chr(0xDC00)])
@pytest.mark.parametrize("unicode_escape", [False, True])
def test_literal_surrogates_keep_the_existing_validation(
    units: str, *, unicode_escape: bool
) -> None:
    key = "café/" + units
    value = "/" + _token(key)
    if unicode_escape:
        with pytest.raises(UnicodeEncodeError):
            JSONPointer(value, unicode_escape=unicode_escape)
    else:
        assert (
            JSONPointer(value, unicode_escape=unicode_escape).resolve({key: _VALUE})
            == _VALUE
        )
