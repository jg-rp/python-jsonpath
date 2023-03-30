import jsonpath


def test_match_string_repr() -> None:
    matches = list(jsonpath.finditer("$.*", ["thing"]))
    assert len(matches) == 1
    assert str(matches[0]) == "'thing' @ $[0]"


def test_truncate_match_string_repr() -> None:
    matches = list(
        jsonpath.finditer("$.*", ["something long that needs to be truncated"])
    )
    assert len(matches) == 1
    assert str(matches[0]) == "'something long that needs to...' @ $[0]"
