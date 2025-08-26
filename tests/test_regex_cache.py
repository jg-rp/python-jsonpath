try:
    import iregexp_check  # noqa: F401

    IREGEXP_AVAILABLE = True
except ImportError:
    IREGEXP_AVAILABLE = False

import pytest

from jsonpath import JSONPathError
from jsonpath.function_extensions import Search


def test_patterns_are_cached() -> None:
    search_func = Search(cache_capacity=2)
    assert len(search_func.cache) == 0
    assert search_func("abcdef", "bc.")
    assert len(search_func.cache) == 1


def test_malformed_patterns_are_cached() -> None:
    search_func = Search(cache_capacity=2)
    assert len(search_func.cache) == 0
    assert search_func("abcdef", "bc[") is False
    assert len(search_func.cache) == 1
    assert search_func.cache["bc["] is None


@pytest.mark.skipif(IREGEXP_AVAILABLE is False, reason="requires iregexp_check")
def test_invalid_iregexp_patterns_are_cached() -> None:
    search_func = Search(cache_capacity=2)
    assert len(search_func.cache) == 0
    assert search_func("ab123cdef", "\\d+") is False
    assert len(search_func.cache) == 1
    assert search_func.cache["\\d+"] is None


def test_debug_regex_patterns() -> None:
    search_func = Search(cache_capacity=2, debug=True)
    assert len(search_func.cache) == 0

    with pytest.raises(JSONPathError):
        search_func("abcdef", "bc[")


def test_cache_capacity() -> None:
    search_func = Search(cache_capacity=2)
    assert len(search_func.cache) == 0
    assert search_func("1abcdef", "ab[a-z]")
    assert len(search_func.cache) == 1
    assert search_func("2abcdef", "bc[a-z]")
    assert len(search_func.cache) == 2  # noqa: PLR2004
    assert search_func("3abcdef", "cd[a-z]")
    assert len(search_func.cache) == 2  # noqa: PLR2004
    assert "cd[a-z]" in search_func.cache
    assert "bc[a-z]" in search_func.cache
    assert "ab[a-z]" not in search_func.cache
