"""Test cases for the fluent API."""
import pytest

from jsonpath import query


def test_iter_query() -> None:
    """Test that `query` result is iterable, just like `finditer`."""
    it = query("$.some.*", {"some": [0, 1, 2, 3]})
    for i, match in enumerate(it):
        assert match.value == i

    assert [m.obj for m in query("$.some.*", {"some": [0, 1, 2, 3]})] == [0, 1, 2, 3]


def test_query_values() -> None:
    """Test that we can get an iterable of values from a query."""
    it = query("$.some.*", {"some": [0, 1, 2, 3]}).values()
    assert list(it) == [0, 1, 2, 3]


def test_query_locations() -> None:
    """Test that we can get an iterable of paths from a query."""
    it = query("$.some.*", {"some": [0, 1, 2, 3]}).locations()
    assert list(it) == [
        "$['some'][0]",
        "$['some'][1]",
        "$['some'][2]",
        "$['some'][3]",
    ]


def test_query_items() -> None:
    """Test that we can get an iterable of values and paths from a query."""
    it = query("$.some.*", {"some": [0, 1, 2, 3]}).items()
    assert list(it) == [
        ("$['some'][0]", 0),
        ("$['some'][1]", 1),
        ("$['some'][2]", 2),
        ("$['some'][3]", 3),
    ]


def test_query_skip() -> None:
    """Test that we can skip matches from the start of a query iterable."""
    it = query("$.some.*", {"some": [0, 1, 2, 3]}).skip(2)
    matches = list(it)
    assert len(matches) == 2  # noqa: PLR2004
    assert [m.obj for m in matches] == [2, 3]


def test_query_skip_zero() -> None:
    """Test that we can skip zero matches from the start of a query iterable."""
    it = query("$.some.*", {"some": [0, 1, 2, 3]}).skip(0)
    matches = list(it)
    assert len(matches) == 4  # noqa: PLR2004
    assert [m.obj for m in matches] == [0, 1, 2, 3]


def test_query_skip_negative() -> None:
    """Test that we get an exception when skipping a negative value."""
    with pytest.raises(ValueError, match="can't drop a negative number of matches"):
        query("$.some.*", {"some": [0, 1, 2, 3]}).skip(-1)


def test_query_skip_all() -> None:
    """Test that we can skip all matches from the start of a query iterable."""
    it = query("$.some.*", {"some": [0, 1, 2, 3]}).skip(4)
    matches = list(it)
    assert len(matches) == 0  # noqa: PLR2004
    assert [m.obj for m in matches] == []


def test_query_skip_more() -> None:
    """Test that we can skip more results than there are matches."""
    it = query("$.some.*", {"some": [0, 1, 2, 3]}).skip(5)
    matches = list(it)
    assert len(matches) == 0  # noqa: PLR2004
    assert [m.obj for m in matches] == []


def test_query_drop() -> None:
    """Test that we can skip matches with `drop`."""
    it = query("$.some.*", {"some": [0, 1, 2, 3]}).drop(2)
    matches = list(it)
    assert len(matches) == 2  # noqa: PLR2004
    assert [m.obj for m in matches] == [2, 3]
