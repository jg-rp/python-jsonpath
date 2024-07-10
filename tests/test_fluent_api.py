"""Test cases for the fluent API."""

import pytest

from jsonpath import JSONPathMatch
from jsonpath import JSONPointer
from jsonpath import compile
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


def test_query_limit() -> None:
    """Test that we can limit the number of matches."""
    it = query("$.some.*", {"some": [0, 1, 2, 3]}).limit(2)
    matches = list(it)
    assert len(matches) == 2  # noqa: PLR2004
    assert [m.obj for m in matches] == [0, 1]


def test_query_limit_zero() -> None:
    """Test that we can call limit with zero."""
    it = query("$.some.*", {"some": [0, 1, 2, 3]}).limit(0)
    matches = list(it)
    assert len(matches) == 0  # noqa: PLR2004
    assert [m.obj for m in matches] == []


def test_query_limit_more() -> None:
    """Test that we can give limit a number greater than the number of matches."""
    it = query("$.some.*", {"some": [0, 1, 2, 3]}).limit(5)
    matches = list(it)
    assert len(matches) == 4  # noqa: PLR2004
    assert [m.obj for m in matches] == [0, 1, 2, 3]


def test_query_limit_all() -> None:
    """Test limit is number of matches."""
    it = query("$.some.*", {"some": [0, 1, 2, 3]}).limit(4)
    matches = list(it)
    assert len(matches) == 4  # noqa: PLR2004
    assert [m.obj for m in matches] == [0, 1, 2, 3]


def test_query_limit_negative() -> None:
    """Test that we get an exception if limit is negative."""
    with pytest.raises(ValueError, match="can't limit by a negative number of matches"):
        query("$.some.*", {"some": [0, 1, 2, 3]}).limit(-1)


def test_query_head() -> None:
    """Test that we can limit the number of matches with `head`."""
    it = query("$.some.*", {"some": [0, 1, 2, 3]}).head(2)
    matches = list(it)
    assert len(matches) == 2  # noqa: PLR2004
    assert [m.obj for m in matches] == [0, 1]


def test_query_first() -> None:
    """Test that we can limit the number of matches with `first`."""
    it = query("$.some.*", {"some": [0, 1, 2, 3]}).first(2)
    matches = list(it)
    assert len(matches) == 2  # noqa: PLR2004
    assert [m.obj for m in matches] == [0, 1]


def test_query_tail() -> None:
    """Test that we can get the last _n_ matches."""
    it = query("$.some.*", {"some": [0, 1, 2, 3]}).tail(2)
    matches = list(it)
    assert len(matches) == 2  # noqa: PLR2004
    assert [m.obj for m in matches] == [2, 3]


def test_query_tail_zero() -> None:
    """Test that we can call `tail` with zero."""
    it = query("$.some.*", {"some": [0, 1, 2, 3]}).tail(0)
    matches = list(it)
    assert len(matches) == 0  # noqa: PLR2004
    assert [m.obj for m in matches] == []


def test_query_tail_all() -> None:
    """Test tail is the same as the number of matches."""
    it = query("$.some.*", {"some": [0, 1, 2, 3]}).tail(4)
    matches = list(it)
    assert len(matches) == 4  # noqa: PLR2004
    assert [m.obj for m in matches] == [0, 1, 2, 3]


def test_query_tail_more() -> None:
    """Test tail is more than the number of matches."""
    it = query("$.some.*", {"some": [0, 1, 2, 3]}).tail(5)
    matches = list(it)
    assert len(matches) == 4  # noqa: PLR2004
    assert [m.obj for m in matches] == [0, 1, 2, 3]


def test_query_tail_negative() -> None:
    """Test that we get an exception if tail is given a negative integer."""
    with pytest.raises(ValueError, match="can't select a negative number of matches"):
        query("$.some.*", {"some": [0, 1, 2, 3]}).tail(-1)


def test_query_last() -> None:
    """Test that we can get the last _n_ matches with `last`."""
    it = query("$.some.*", {"some": [0, 1, 2, 3]}).last(2)
    matches = list(it)
    assert len(matches) == 2  # noqa: PLR2004
    assert [m.obj for m in matches] == [2, 3]


def test_query_first_one() -> None:
    """Test that we can get the first match from a query iterator."""
    maybe_match = query("$.some.*", {"some": [0, 1, 2, 3]}).first_one()
    assert isinstance(maybe_match, JSONPathMatch)
    assert maybe_match.value == 0


def test_query_first_one_of_empty_iterator() -> None:
    """Test that `first_one` returns `None` if the iterator is empty."""
    maybe_match = query("$.nosuchthing.*", {"some": [0, 1, 2, 3]}).first_one()
    assert maybe_match is None


def test_query_one() -> None:
    """Test that we can get the first match from a query iterator with `one`."""
    maybe_match = query("$.some.*", {"some": [0, 1, 2, 3]}).one()
    assert isinstance(maybe_match, JSONPathMatch)
    assert maybe_match.value == 0


def test_query_last_one() -> None:
    """Test that we can get the last match from a query iterator."""
    maybe_match = query("$.some.*", {"some": [0, 1, 2, 3]}).last_one()
    assert isinstance(maybe_match, JSONPathMatch)
    assert maybe_match.value == 3  # noqa: PLR2004


def test_query_last_of_empty_iterator() -> None:
    """Test that `last_one` returns `None` if the iterator is empty."""
    maybe_match = query("$.nosuchthing.*", {"some": [0, 1, 2, 3]}).last_one()
    assert maybe_match is None


def test_query_tee() -> None:
    """Test that we can tee a query iterator."""
    it1, it2 = query("$.some.*", {"some": [0, 1, 2, 3]}).tee()

    rv1 = it1.skip(1).one()
    assert rv1 is not None
    assert rv1.value == 1

    rv2 = it2.skip(2).one()
    assert rv2 is not None
    assert rv2.value == 2  # noqa: PLR2004


def test_query_pointers() -> None:
    """Test that we can get pointers from a query."""
    pointers = list(query("$.some.*", {"some": [0, 1, 2, 3]}).pointers())
    assert len(pointers) == 4  # noqa: PLR2004
    assert pointers[0] == JSONPointer("/some/0")


def test_query_take() -> None:
    """Test that we can take matches from a query iterable."""
    it = query("$.some.*", {"some": [0, 1, 2, 3]})
    head = list(it.take(2).values())
    assert len(head) == 2  # noqa: PLR2004
    assert head == [0, 1]
    assert list(it.values()) == [2, 3]


def test_query_take_all() -> None:
    """Test that we can take all matches from a query iterable."""
    it = query("$.some.*", {"some": [0, 1, 2, 3]})
    head = list(it.take(4).values())
    assert len(head) == 4  # noqa: PLR2004
    assert head == [0, 1, 2, 3]
    assert list(it.values()) == []


def test_query_take_more() -> None:
    """Test that we can take more matches than there are nodes."""
    it = query("$.some.*", {"some": [0, 1, 2, 3]})
    head = list(it.take(5).values())
    assert len(head) == 4  # noqa: PLR2004
    assert head == [0, 1, 2, 3]
    assert list(it.values()) == []


def test_query_from_compiled_path() -> None:
    """Test that we can get a query iterator from a compiled path."""
    path = compile("$.some.*")
    it = path.query({"some": [0, 1, 2, 3]}).values()
    assert list(it) == [0, 1, 2, 3]
