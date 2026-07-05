r"""Regression tests for lexing string literals containing escaped backslashes.

The lexer used to detect the closing quote of a string literal with a
look-behind that only checked for a single preceding backslash. That mistook a
quote following an *escaped* backslash (``\\``) for an *escaped* quote (``\'``),
so any name selector whose value ended in an even-length run of backslashes
failed to tokenize. This also broke the RFC 9535 normalized-path round-trip:
python-jsonpath produced ``match.path`` strings it could not parse back.
"""

from typing import Any
from typing import List

import pytest

import jsonpath


@pytest.mark.parametrize(
    ("query", "document", "want"),
    [
        # A single-quoted name selector whose value ends with a backslash,
        # followed by another selector (the shape a normalized path takes).
        (r"$['a\\']['b']", {"a\\": {"b": 1}}, [1]),
        # Double-quoted variant.
        (r'$["a\\"]["b"]', {"a\\": {"b": 2}}, [2]),
        # Backslash key indexing into a list.
        (r"$['\\'][0]", {"\\": [9]}, [9]),
        # Two consecutive backslash keys.
        (r"$['x\\']['y\\']", {"x\\": {"y\\": 5}}, [5]),
        # Value that is two backslashes.
        (r"$['\\\\']['b']", {"\\\\": {"b": 7}}, [7]),
        # Escaped backslash followed by an escaped quote in the same literal.
        (r"$['a\\\'b']", {"a\\'b": 3}, [3]),
        # A trailing backslash selector on its own still works.
        (r"$['a\\']", {"a\\": 4}, [4]),
        # Escaped quote (no backslash bug) must keep working.
        (r"$['a\'b']", {"a'b": 6}, [6]),
    ],
)
def test_escaped_backslash_string_literals(
    query: str, document: Any, want: List[Any]
) -> None:
    assert jsonpath.findall(query, document) == want


# Documents whose keys exercise backslashes, quotes and control characters.
ROUND_TRIP_DOCUMENTS: List[Any] = [
    {"a\\": {"b": 1}},
    {"trailing\\": [1, 2, 3]},
    {"\\": {"\\": {"\\": 0}}},
    {"x\\": {"y\\": {"z\\": 42}}},
    {"a\\'b": 1, "c\\\\d": 2, "e'f": 3},
    {"mix\\ed": [{"k\\": "v"}]},
    {"back\\slash": 1, "quote'": 2, "both\\'": 3},
]


@pytest.mark.parametrize("document", ROUND_TRIP_DOCUMENTS)
def test_normalized_path_round_trip(document: Any) -> None:
    """Every normalized path must select exactly the node it came from."""
    for match in jsonpath.finditer("$..*", document):
        nodes = list(jsonpath.finditer(match.path, document))
        assert len(nodes) == 1, f"{match.path!r} selected {len(nodes)} nodes"
        assert nodes[0].parts == match.parts
        assert nodes[0].value == match.value


@pytest.mark.parametrize("document", ROUND_TRIP_DOCUMENTS)
def test_normalized_path_is_idempotent(document: Any) -> None:
    """Re-normalizing a normalized path yields the same path."""
    for match in jsonpath.finditer("$..*", document):
        (again,) = jsonpath.finditer(match.path, document)
        assert again.path == match.path
