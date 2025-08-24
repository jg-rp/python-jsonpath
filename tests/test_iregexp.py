import pytest

try:
    import iregexp_check  # noqa: F401

    IREGEXP_AVAILABLE = True
except ImportError:
    IREGEXP_AVAILABLE = False

import jsonpath


@pytest.mark.skipif(IREGEXP_AVAILABLE is False, reason="requires iregexp_check")
def test_iregexp_check() -> None:
    # Character classes are OK.
    query = "$[?match(@, '[0-9]+')]"
    data = ["123", "abc", "abc123"]
    assert jsonpath.findall(query, data) == ["123"]

    # Multi character escapes are not.
    query = "$[?match(@, '\\\\d+')]"
    assert jsonpath.findall(query, data) == []


@pytest.mark.skipif(IREGEXP_AVAILABLE, reason="iregexp_check is available")
def test_no_iregexp_check() -> None:
    # Character classes are OK.
    query = "$[?match(@, '[0-9]+')]"
    data = ["123", "abc", "abc123"]
    assert jsonpath.findall(query, data) == ["123"]

    # Multi character escapes are OK when iregexp_check is not installed.
    query = "$[?match(@, '\\\\d+')]"
    assert jsonpath.findall(query, data) == ["123"]
