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


def test_parent_match() -> None:
    matches = list(jsonpath.finditer("$.some.thing", {"some": {"thing": "else"}}))
    assert len(matches) == 1
    assert matches[0].obj == "else"
    assert matches[0].parent is not None
    assert matches[0].parent.obj == {"thing": "else"}
    assert matches[0].parent.path == "$['some']"


def test_match_parts() -> None:
    matches = list(jsonpath.finditer("$.some.thing", {"some": {"thing": "else"}}))
    assert len(matches) == 1
    assert matches[0].obj == "else"
    assert matches[0].parts == ("some", "thing")


def test_child_matches() -> None:
    matches = list(jsonpath.finditer("$.things.*", {"things": ["foo", "bar"]}))
    assert len(matches) == 2  # noqa: PLR2004
    assert matches[0].obj == "foo"
    assert matches[1].obj == "bar"
    assert matches[0].parent is not None

    children = matches[0].parent.children
    assert len(children) == 2  # noqa: PLR2004
    assert children[0].obj == "foo"
    assert children[1].obj == "bar"
